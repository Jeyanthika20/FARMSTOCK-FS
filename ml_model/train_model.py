"""
FarmStock - Crop Price Prediction ML Pipeline  (v2 — FIXED & ENHANCED)
=======================================================================
CHANGES FROM v1:
  FIX 1  - Price unit: ALL prices now in Rs/kg (dataset Rs/quintal / 100)
  FIX 2  - Step 5 forecast crash fixed: Timestamp vs datetime.date bug
  NEW 1  - Storage life feature per crop
  NEW 2  - Harvest calendar: weeks_since_harvest, weeks_to_harvest
  NEW 3  - Competition index: # markets reporting same crop same day
  NEW 4  - State median price (inter-state trade signal)
  NEW 5  - Supply proxy feature
  NEW 6  - Market price count feature
  NEW 7  - Festival dates extended to 2026
  NEW 8  - XGBoost optional (graceful fallback if not installed)
"""

import pandas as pd
import numpy as np
import warnings
import os
import joblib
import json
from datetime import datetime, timedelta, date as date_type

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not installed - training RF, GB, Ridge only")

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Price_Agriculture_commodities_Week.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------- Reference Data ----------
VEGETABLES = {'Tomato','Onion','Potato','Brinjal','Cabbage','Cauliflower',
              'Bhindi(Ladies Finger)','Green Chilli','Cucumbar(Kheera)',
              'Bottle Gourd','Bitter Gourd','Pumpkin','Carrot','Garlic',
              'Ginger','Capsicum','Spinach','Coriander'}
GRAINS  = {'Wheat','Rice','Maize','Jowar','Bajra','Barley','Ragi'}
FRUITS  = {'Banana','Mango','Apple','Grapes','Pomegranate','Papaya',
           'Watermelon','Orange','Lemon'}
SPICES  = {'Turmeric','Coriander Seed','Cumin','Fennel','Fenugreek',
           'Mustard','Pepper','Cardamom','Clove'}
PERISHABLE = {'Tomato','Spinach','Coriander','Green Chilli','Bhindi(Ladies Finger)',
              'Bottle Gourd','Cucumbar(Kheera)','Brinjal','Capsicum'}

STORAGE_LIFE = {
    'Tomato':7,'Spinach':3,'Coriander':4,'Green Chilli':10,
    'Bhindi(Ladies Finger)':4,'Bottle Gourd':7,'Brinjal':7,'Capsicum':14,
    'Potato':180,'Onion':120,'Garlic':180,'Cabbage':30,'Cauliflower':14,
    'Carrot':30,'Pumpkin':90,'Wheat':365,'Rice':365,'Maize':180,
    'Jowar':180,'Bajra':180,'Banana':7,'Mango':14,'Apple':90,'Grapes':14,
    'Turmeric':365,'Cumin':365,
}

HARVEST_CALENDAR = {
    'Wheat':(11,4),'Rice':(7,11),'Maize':(6,9),'Tomato':(11,3),
    'Onion':(11,3),'Potato':(11,2),'Mango':(3,6),'Banana':(1,12),
    'Turmeric':(6,1),'Cumin':(11,2),'Garlic':(10,3),'Jowar':(7,10),
}

FESTIVAL_DATES = pd.to_datetime([
    '2023-10-24','2024-11-01','2025-10-20','2026-11-08',
    '2023-03-08','2024-03-25','2025-03-14','2026-03-03',
    '2023-04-22','2024-04-10','2025-03-31','2026-03-20',
    '2023-10-02','2024-10-03','2025-09-22','2026-10-11',
    '2023-01-14','2024-01-14','2025-01-14','2026-01-14',
    '2023-08-15','2024-08-15','2025-08-15','2026-08-15',
    '2024-04-14','2025-04-14','2026-04-14',
])


def get_season(month):
    if month in [6,7,8,9,10]:   return 'Kharif'
    elif month in [11,12,1,2,3]: return 'Rabi'
    else:                         return 'Zaid'


def get_crop_category(crop):
    if crop in VEGETABLES: return 'vegetable'
    if crop in GRAINS:     return 'grain'
    if crop in FRUITS:     return 'fruit'
    if crop in SPICES:     return 'spice'
    return 'other'


def days_to_nearest_festival(d):
    """FIX: normalize to date object so Timestamp - date.date TypeError never occurs."""
    if hasattr(d, 'date'):
        d = d.date()
    elif not isinstance(d, date_type):
        d = pd.to_datetime(d).date()
    diffs = []
    for f in FESTIVAL_DATES:
        f_d = f.date() if hasattr(f, 'date') else f
        diff = (d - f_d).days
        if -30 <= diff <= 5:
            diffs.append(abs(diff))
    return min(diffs) if diffs else 30


def get_harvest_features(crop, d):
    if hasattr(d, 'date'):
        d = d.date()
    elif not isinstance(d, date_type):
        d = pd.to_datetime(d).date()
    cal = HARVEST_CALENDAR.get(str(crop))
    if cal is None:
        return 26, 26
    harvest_month = cal[1]
    m = d.month
    return (m - harvest_month) % 12 * 4, (harvest_month - m) % 12 * 4


# ==================== STEP 1 ====================
def load_and_clean(path):
    print("\n" + "="*60)
    print("STEP 1: LOADING & CLEANING DATA")
    print("="*60)

    df = pd.read_csv(path)
    print(f"  Raw records: {len(df):,}")

    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df.rename(columns={'arrival_date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df.dropna(subset=['date'], inplace=True)

    for col in ['state','district','market','commodity','variety','grade']:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title()

    # FIX 1: Convert Rs/quintal -> Rs/kg
    for col in ['min_price','max_price','modal_price']:
        if col in df.columns:
            df[col] = df[col] / 100.0

    # Valid Rs/kg range
    df = df[(df['modal_price'] >= 0.50) & (df['modal_price'] <= 2000.0)]

    before = len(df)
    df.drop_duplicates(subset=['date','commodity','market'], keep='first', inplace=True)
    print(f"  Duplicates removed: {before - len(df)}")

    df['min_price'] = df['min_price'].fillna(df['modal_price'] * 0.9)
    df['max_price'] = df['max_price'].fillna(df['modal_price'] * 1.1)

    print(f"  Clean records: {len(df):,}")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  Unique crops: {df['commodity'].nunique()}")
    print(f"  Price unit: Rs/kg  (converted from Rs/quintal)")
    print(f"  Target range: Rs{df['modal_price'].min():.2f} - Rs{df['modal_price'].max():.2f}/kg")
    return df.reset_index(drop=True)


# ==================== STEP 2 ====================
def engineer_features(df):
    print("\n" + "="*60)
    print("STEP 2: FEATURE ENGINEERING  (44 features)")
    print("="*60)

    df = df.sort_values(['commodity','market','date']).reset_index(drop=True)

    # Temporal
    df['year']        = df['date'].dt.year
    df['month']       = df['date'].dt.month
    df['week']        = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_year'] = df['date'].dt.dayofyear
    df['is_weekend']  = (df['day_of_week'] >= 5).astype(int)
    df['quarter']     = df['date'].dt.quarter

    # Season
    df['season'] = df['month'].apply(get_season)

    # Festival (FIXED)
    print("  Festival proximity...")
    df['days_to_festival']   = df['date'].apply(days_to_nearest_festival)
    df['is_festival_season'] = (df['days_to_festival'] <= 14).astype(int)

    # Weather
    temp_map = {1:15,2:18,3:24,4:30,5:35,6:34,7:30,8:29,9:28,10:25,11:20,12:16}
    rain_map = {1:10,2:12,3:15,4:20,5:35,6:150,7:280,8:260,9:180,10:80,11:25,12:12}
    df['temp_proxy']     = df['month'].map(temp_map)
    df['rainfall_proxy'] = df['month'].map(rain_map)
    df['is_monsoon']     = df['month'].isin([6,7,8,9]).astype(int)

    # Price spread
    df['price_spread'] = (df['max_price'] - df['min_price']) / (df['modal_price'] + 0.01)

    # Crop attributes
    df['crop_category']     = df['commodity'].apply(get_crop_category)
    df['is_perishable']     = df['commodity'].isin(PERISHABLE).astype(int)
    df['storage_life_days'] = df['commodity'].map(STORAGE_LIFE).fillna(60)

    # Harvest calendar (NEW)
    print("  Harvest calendar features...")
    hf = df.apply(lambda r: pd.Series(get_harvest_features(r['commodity'], r['date'])), axis=1)
    df['weeks_since_harvest'] = hf[0].values
    df['weeks_to_harvest']    = hf[1].values

    # Lag & rolling
    print("  Lag & rolling stats...")
    grp = df.groupby(['commodity','market'])['modal_price']
    df['lag_7']  = grp.shift(7)
    df['lag_14'] = grp.shift(14)
    df['lag_30'] = grp.shift(30)
    df['rolling_mean_7']  = grp.transform(lambda x: x.rolling(7,  min_periods=1).mean())
    df['rolling_mean_14'] = grp.transform(lambda x: x.rolling(14, min_periods=1).mean())
    df['rolling_mean_30'] = grp.transform(lambda x: x.rolling(30, min_periods=1).mean())
    df['rolling_std_7']   = grp.transform(lambda x: x.rolling(7,  min_periods=1).std().fillna(0))
    df['rolling_std_30']  = grp.transform(lambda x: x.rolling(30, min_periods=1).std().fillna(0))

    # Momentum
    df['price_change_pct'] = grp.pct_change().fillna(0).clip(-1, 2)

    # Market rank
    df['market_price_rank'] = df.groupby(['date','commodity'])['modal_price'].rank(pct=True).fillna(0.5)

    # NEW features
    df['competition_index']   = df.groupby(['date','commodity'])['market'].transform('count').fillna(1)
    df['state_median_price']  = df.groupby(['date','commodity','state'])['modal_price'].transform('median').fillna(df['modal_price'])
    df['market_price_count']  = df.groupby(['date','market'])['commodity'].transform('count').fillna(1)
    commodity_avg             = df.groupby('commodity')['date'].transform('count')
    total_days                = max(df['date'].nunique(), 1)
    df['supply_proxy']        = (df['competition_index'] / (commodity_avg / total_days + 0.01)).clip(0, 10)

    # Cyclical
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dow_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)

    # Fill NaN lags
    for col in ['lag_7','lag_14','lag_30']:
        df[col] = df[col].fillna(df.groupby('commodity')['modal_price'].transform('median'))

    print(f"  Done. Total columns: {len(df.columns)}")
    return df


# ==================== STEP 3 ====================
def prepare_ml_data(df):
    print("\n" + "="*60)
    print("STEP 3: ENCODING & PREPARING ML DATA")
    print("="*60)

    cat_cols = ['state','district','market','commodity','variety','grade','season','crop_category']
    encoders = {}
    for col in cat_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col + '_enc'] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    FEATURES = [
        'state_enc','district_enc','market_enc','commodity_enc','variety_enc','grade_enc','season_enc','crop_category_enc',
        'year','month','week','day_of_week','day_of_year','quarter','is_weekend',
        'month_sin','month_cos','dow_sin','dow_cos',
        'temp_proxy','rainfall_proxy','is_monsoon',
        'days_to_festival','is_festival_season',
        'min_price','max_price','price_spread',
        'lag_7','lag_14','lag_30',
        'rolling_mean_7','rolling_mean_14','rolling_mean_30','rolling_std_7','rolling_std_30',
        'price_change_pct',
        'is_perishable','market_price_rank','storage_life_days',
        'weeks_since_harvest','weeks_to_harvest',
        'competition_index','state_median_price','market_price_count','supply_proxy',
    ]
    FEATURES = [f for f in FEATURES if f in df.columns]

    df_model = df[FEATURES + ['modal_price']].dropna()
    X = df_model[FEATURES].values
    y = df_model['modal_price'].values

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"  Features: {len(FEATURES)}")
    print(f"  Samples : {len(X):,}")
    print(f"  Target  : Rs/kg  range Rs{y.min():.2f} - Rs{y.max():.2f}/kg")
    return X, y, X_scaled, FEATURES, encoders, scaler, df_model


# ==================== STEP 4 ====================
def train_and_evaluate(X, y, X_scaled, feature_names):
    print("\n" + "="*60)
    print("STEP 4: TRAINING MODELS")
    print("="*60)

    split = int(len(X) * 0.8)
    X_tr, X_te   = X[:split], X[split:]
    y_tr, y_te   = y[:split], y[split:]
    Xs_tr, Xs_te = X_scaled[:split], X_scaled[split:]
    print(f"  Train: {len(X_tr):,}  Test: {len(X_te):,}")

    results = {}

    if XGBOOST_AVAILABLE:
        print("\n  [1] XGBoost...")
        m = xgb.XGBRegressor(n_estimators=500,learning_rate=0.05,max_depth=7,
                              subsample=0.8,colsample_bytree=0.8,min_child_weight=5,
                              reg_alpha=0.1,reg_lambda=1.0,random_state=42,n_jobs=-1,verbosity=0)
        m.fit(X_tr, y_tr, eval_set=[(X_te,y_te)], early_stopping_rounds=30, verbose=False)
        p = m.predict(X_te)
        results['XGBoost'] = {'model':m,'preds':p,'mae':mean_absolute_error(y_te,p),
            'rmse':np.sqrt(mean_squared_error(y_te,p)),'r2':r2_score(y_te,p),
            'mape':np.mean(np.abs((y_te-p)/(y_te+0.01)))*100}

    print("\n  [2] Random Forest...")
    m = RandomForestRegressor(n_estimators=300,max_depth=15,min_samples_leaf=5,n_jobs=-1,random_state=42)
    m.fit(X_tr, y_tr)
    p = m.predict(X_te)
    results['RandomForest'] = {'model':m,'preds':p,'mae':mean_absolute_error(y_te,p),
        'rmse':np.sqrt(mean_squared_error(y_te,p)),'r2':r2_score(y_te,p),
        'mape':np.mean(np.abs((y_te-p)/(y_te+0.01)))*100}

    print("  [3] Gradient Boosting...")
    m = GradientBoostingRegressor(n_estimators=300,learning_rate=0.05,max_depth=5,subsample=0.8,random_state=42)
    m.fit(X_tr, y_tr)
    p = m.predict(X_te)
    results['GradientBoosting'] = {'model':m,'preds':p,'mae':mean_absolute_error(y_te,p),
        'rmse':np.sqrt(mean_squared_error(y_te,p)),'r2':r2_score(y_te,p),
        'mape':np.mean(np.abs((y_te-p)/(y_te+0.01)))*100}

    print("  [4] Ridge (baseline)...")
    m = Ridge(alpha=1.0)
    m.fit(Xs_tr, y_tr)
    p = m.predict(Xs_te)
    results['Ridge'] = {'model':m,'preds':p,'mae':mean_absolute_error(y_te,p),
        'rmse':np.sqrt(mean_squared_error(y_te,p)),'r2':r2_score(y_te,p),
        'mape':np.mean(np.abs((y_te-p)/(y_te+0.01)))*100}

    print("\n" + "-"*70)
    print(f"{'Model':<20} {'MAE Rs/kg':>12} {'RMSE':>10} {'R2':>8} {'MAPE%':>8}")
    print("-"*70)
    for name, res in results.items():
        print(f"{name:<20} {res['mae']:>12.3f} {res['rmse']:>10.3f} {res['r2']:>8.4f} {res['mape']:>8.2f}%")
    print("-"*70)

    best = min(results, key=lambda k: results[k]['mae'])
    print(f"\n  Best: {best}  MAE=Rs{results[best]['mae']:.3f}/kg  R2={results[best]['r2']:.4f}")
    return results, best, y_te, split


# ==================== STEP 5: FORECAST (FIXED) ====================
def forecast_future(model, df_feat, feature_names, encoders, scaler,
                    commodity='Tomato', market=None, horizon_days=30):
    """Rolling forecast. FIX: All dates normalized to datetime.date."""
    if market is None:
        market = df_feat[df_feat['commodity'].str.title() == commodity.title()]['market'].value_counts().index[0]

    subset = df_feat[(df_feat['commodity'].str.title() == commodity.title()) &
                     (df_feat['market'] == market)].sort_values('date').copy()
    if len(subset) == 0:
        raise ValueError(f"No data for {commodity} / {market}")

    last_row  = subset.iloc[-1]
    # CRITICAL FIX: normalize to Python date
    last_date = last_row['date'].date() if hasattr(last_row['date'], 'date') else last_row['date']
    recent    = list(subset['modal_price'].values[-30:])
    forecasts = []

    temp_map = {1:15,2:18,3:24,4:30,5:35,6:34,7:30,8:29,9:28,10:25,11:20,12:16}
    rain_map = {1:10,2:12,3:15,4:20,5:35,6:150,7:280,8:260,9:180,10:80,11:25,12:12}

    for i in range(1, horizon_days + 1):
        fd = last_date + timedelta(days=i)   # datetime.date
        m  = fd.month
        row = {}

        for col in ['state','district','market','commodity','variety','grade']:
            val = str(last_row.get(col, ''))
            le  = encoders.get(col)
            if le:
                try:    row[col+'_enc'] = int(le.transform([val])[0])
                except: row[col+'_enc'] = 0

        season = get_season(m)
        le_s   = encoders.get('season')
        row['season_enc'] = int(le_s.transform([season])[0]) if le_s else 0

        cc   = str(last_row.get('crop_category','vegetable'))
        le_cc = encoders.get('crop_category')
        if le_cc:
            try:    row['crop_category_enc'] = int(le_cc.transform([cc])[0])
            except: row['crop_category_enc'] = 0

        row.update({'year':fd.year,'month':m,'week':fd.isocalendar()[1],
                    'day_of_week':fd.weekday(),'day_of_year':fd.timetuple().tm_yday,
                    'quarter':(m-1)//3+1,'is_weekend':int(fd.weekday()>=5),
                    'month_sin':np.sin(2*np.pi*m/12),'month_cos':np.cos(2*np.pi*m/12),
                    'dow_sin':np.sin(2*np.pi*fd.weekday()/7),'dow_cos':np.cos(2*np.pi*fd.weekday()/7),
                    'temp_proxy':temp_map[m],'rainfall_proxy':rain_map[m],'is_monsoon':int(m in [6,7,8,9]),
                    'days_to_festival':days_to_nearest_festival(fd),
                    })
        row['is_festival_season'] = int(row['days_to_festival'] <= 14)

        r = recent[-30:] if len(recent) >= 30 else recent
        row['min_price']    = np.percentile(r, 10)
        row['max_price']    = np.percentile(r, 90)
        row['price_spread'] = (row['max_price'] - row['min_price']) / (np.mean(r) + 0.01)
        row['lag_7']        = recent[-7]  if len(recent)>=7  else np.mean(recent)
        row['lag_14']       = recent[-14] if len(recent)>=14 else np.mean(recent)
        row['lag_30']       = recent[-30] if len(recent)>=30 else np.mean(recent)
        row['rolling_mean_7']  = np.mean(recent[-7:])
        row['rolling_mean_14'] = np.mean(recent[-14:]) if len(recent)>=14 else np.mean(recent)
        row['rolling_mean_30'] = np.mean(recent)
        row['rolling_std_7']   = np.std(recent[-7:])  if len(recent)>=7  else 0
        row['rolling_std_30']  = np.std(recent)        if len(recent)>=2  else 0
        row['price_change_pct'] = (recent[-1]-recent[-2])/(recent[-2]+0.01) if len(recent)>=2 else 0

        row['is_perishable']       = int(last_row.get('is_perishable',1))
        row['market_price_rank']   = 0.5
        row['storage_life_days']   = STORAGE_LIFE.get(commodity, 60)
        wsh, wth                   = get_harvest_features(commodity, fd)
        row['weeks_since_harvest'] = wsh
        row['weeks_to_harvest']    = wth
        row['competition_index']   = float(last_row.get('competition_index', 5))
        row['state_median_price']  = float(np.mean(recent))
        row['market_price_count']  = float(last_row.get('market_price_count', 10))
        row['supply_proxy']        = 1.0

        fv   = np.array([[row.get(f, 0) for f in feature_names]])
        pred = max(0.5, float(model.predict(fv)[0]))

        forecasts.append({'date':fd.strftime('%Y-%m-%d'),'day':i,
                          'predicted_price_kg':round(pred,2),
                          'predicted_price_quintal':round(pred*100,2),
                          'commodity':commodity,'market':market})
        recent.append(pred)

    return pd.DataFrame(forecasts)


# ==================== STEP 6: SAVE ====================
def save_artifacts(results, best_name, encoders, scaler, feature_names, df_clean):
    print("\n" + "="*60)
    print("STEP 6: SAVING ARTIFACTS")
    print("="*60)

    joblib.dump(results[best_name]['model'], os.path.join(MODEL_DIR,'best_model.pkl'))
    joblib.dump(encoders,                    os.path.join(MODEL_DIR,'encoders.pkl'))
    joblib.dump(scaler,                      os.path.join(MODEL_DIR,'scaler.pkl'))
    for name, res in results.items():
        joblib.dump(res['model'], os.path.join(MODEL_DIR,f'{name.lower()}_model.pkl'))

    meta = {
        'best_model':    best_name,
        'feature_names': feature_names,
        'price_unit':    'INR_per_kg',
        'trained_at':    datetime.now().isoformat(),
        'metrics':       {n:{'mae':round(r['mae'],4),'rmse':round(r['rmse'],4),
                             'r2':round(r['r2'],4),'mape':round(r['mape'],4)}
                          for n,r in results.items()},
        'data_info':     {'total_records':len(df_clean),'unique_crops':df_clean['commodity'].nunique(),
                          'unique_markets':df_clean['market'].nunique(),
                          'date_range':f"{df_clean['date'].min().date()} to {df_clean['date'].max().date()}"},
        'crops_available':   sorted(df_clean['commodity'].unique().tolist()),
        'markets_available': sorted(df_clean['market'].unique().tolist()),
    }
    with open(os.path.join(MODEL_DIR,'metadata.json'),'w') as f:
        json.dump(meta, f, indent=2)

    print(f"  best_model.pkl, encoders.pkl, scaler.pkl, metadata.json saved")
    print(f"  price_unit = INR_per_kg")


# ==================== STEP 7: PLOTS ====================
def save_plots(results, best_name, y_test, df_clean, forecast_df=None):
    fig_dir = os.path.join(MODEL_DIR,'plots')
    os.makedirs(fig_dir, exist_ok=True)

    fig, axes = plt.subplots(2,2,figsize=(14,10))
    axes = axes.flatten()
    for idx,(name,res) in enumerate(results.items()):
        if idx>=4: break
        n = min(200,len(y_test))
        axes[idx].plot(y_test[:n],       label='Actual',    alpha=0.7,color='steelblue')
        axes[idx].plot(res['preds'][:n], label='Predicted', alpha=0.7,color='orange')
        axes[idx].set_title(f"{name}  MAE=Rs{res['mae']:.3f}/kg  R2={res['r2']:.3f}")
        axes[idx].legend(); axes[idx].set_ylabel('Price (Rs/kg)')
    plt.suptitle('FarmStock v2 — Actual vs Predicted (Rs/kg)', fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir,'model_comparison.png'),dpi=120)
    plt.close()

    top_name  = 'XGBoost' if 'XGBoost' in results else 'RandomForest'
    top_model = results[top_name]['model']
    if hasattr(top_model,'feature_importances_'):
        fi = pd.DataFrame({'feature':feat_names,'importance':top_model.feature_importances_}) \
               .sort_values('importance',ascending=True).tail(20)
        plt.figure(figsize=(10,8))
        plt.barh(fi['feature'],fi['importance'],color='#4CAF50')
        plt.title(f'Feature Importance ({top_name})')
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir,'feature_importance.png'),dpi=120)
        plt.close()

    if forecast_df is not None and 'predicted_price_kg' in forecast_df.columns:
        plt.figure(figsize=(12,5))
        plt.plot(forecast_df['day'], forecast_df['predicted_price_kg'],
                 marker='o',color='#FF9800',linewidth=2)
        plt.title(f"30-Day Forecast  {forecast_df['commodity'].iloc[0]} ({forecast_df['market'].iloc[0]})")
        plt.xlabel('Days from Today'); plt.ylabel('Rs/kg'); plt.grid(True,alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir,'price_forecast.png'),dpi=120)
        plt.close()

    print(f"  Plots saved to {fig_dir}/")


# ==================== MAIN ====================
if __name__ == '__main__':
    df_raw   = load_and_clean(DATA_PATH)
    df_feat  = engineer_features(df_raw.copy())
    X, y, Xs, feat_names, encoders, scaler, df_model = prepare_ml_data(df_feat)
    results, best_name, y_test, split_idx = train_and_evaluate(X, y, Xs, feat_names)

    best_model = results[best_name]['model']
    print("\n" + "="*60)
    print("STEP 5: SAMPLE FUTURE PRICE FORECAST")
    print("="*60)
    try:
        top_crop    = df_raw['commodity'].value_counts().index[0]
        forecast_df = forecast_future(best_model, df_feat, feat_names, encoders, scaler,
                                      commodity=top_crop, horizon_days=30)
        print(f"\n  30-day forecast for {top_crop} (Rs/kg):")
        print(forecast_df[['date','predicted_price_kg','predicted_price_quintal']].to_string(index=False))
    except Exception as e:
        import traceback; traceback.print_exc()
        forecast_df = None

    save_artifacts(results, best_name, encoders, scaler, feat_names, df_feat)
    save_plots(results, best_name, y_test, df_feat, forecast_df)

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    best = results[best_name]
    print(f"  Best model : {best_name}")
    print(f"  MAE        : Rs{best['mae']:.3f}/kg  (~Rs{best['mae']*100:.1f}/quintal)")
    print(f"  R2         : {best['r2']:.4f}")
    print(f"  Price unit : Rs/kg  (converted from dataset Rs/quintal)")
    print("="*60)
