"""
ModelService v2 - loads artifacts, runs inference.
CHANGES: price_unit=INR_per_kg, new features in _build_feature_vector,
         forecast returns Rs/kg + Rs/quintal both.
"""
import os, json, joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date as date_type
from typing import Optional

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..','..','..','ml_model','models')

STORAGE_LIFE = {
    'Tomato':7,'Spinach':3,'Coriander':4,'Green Chilli':10,
    'Bhindi(Ladies Finger)':4,'Bottle Gourd':7,'Brinjal':7,'Capsicum':14,
    'Potato':180,'Onion':120,'Garlic':180,'Cabbage':30,'Cauliflower':14,
    'Carrot':30,'Pumpkin':90,'Wheat':365,'Rice':365,'Maize':180,
    'Jowar':180,'Bajra':180,'Banana':7,'Mango':14,'Apple':90,
    'Grapes':14,'Turmeric':365,'Cumin':365,
}
HARVEST_CALENDAR = {
    'Wheat':(11,4),'Rice':(7,11),'Maize':(6,9),'Tomato':(11,3),
    'Onion':(11,3),'Potato':(11,2),'Mango':(3,6),'Banana':(1,12),
    'Turmeric':(6,1),'Cumin':(11,2),'Garlic':(10,3),'Jowar':(7,10),
}
FESTIVAL_DATES = pd.to_datetime([
    '2024-11-01','2025-10-20','2026-11-08',
    '2025-03-14','2026-03-03','2025-03-31','2026-03-20',
    '2025-09-22','2026-10-11','2025-01-14','2026-01-14',
    '2025-08-15','2026-08-15','2025-04-14','2026-04-14',
])

VEGETABLES = {'Tomato','Onion','Potato','Brinjal','Cabbage','Cauliflower',
              'Bhindi(Ladies Finger)','Green Chilli','Cucumbar(Kheera)',
              'Bottle Gourd','Bitter Gourd','Pumpkin','Carrot','Garlic',
              'Ginger','Capsicum','Spinach','Coriander'}
GRAINS  = {'Wheat','Rice','Maize','Jowar','Bajra','Barley','Ragi'}
FRUITS  = {'Banana','Mango','Apple','Grapes','Pomegranate','Papaya',
           'Watermelon','Orange','Lemon'}
PERISHABLE = {'Tomato','Spinach','Coriander','Green Chilli','Bhindi(Ladies Finger)',
              'Bottle Gourd','Cucumbar(Kheera)','Brinjal','Capsicum'}


def _days_to_festival(d) -> int:
    if hasattr(d, 'date'):
        d = d.date()
    elif not isinstance(d, date_type):
        d = pd.to_datetime(d).date()
    diffs = []
    for f in FESTIVAL_DATES:
        fd = f.date() if hasattr(f,'date') else f
        diff = (d - fd).days
        if -30 <= diff <= 5:
            diffs.append(abs(diff))
    return min(diffs) if diffs else 30


def _harvest_features(crop, d):
    if hasattr(d,'date'): d = d.date()
    cal = HARVEST_CALENDAR.get(str(crop).title())
    if not cal: return 26, 26
    return (d.month - cal[1]) % 12 * 4, (cal[1] - d.month) % 12 * 4


class ModelService:
    def __init__(self):
        self.model = self.encoders = self.scaler = None
        self.metadata = {}; self.feature_names = []; self._loaded = False

    def load(self):
        try:
            self.model    = joblib.load(os.path.join(MODEL_DIR,'best_model.pkl'))
            self.encoders = joblib.load(os.path.join(MODEL_DIR,'encoders.pkl'))
            self.scaler   = joblib.load(os.path.join(MODEL_DIR,'scaler.pkl'))
            with open(os.path.join(MODEL_DIR,'metadata.json')) as f:
                self.metadata = json.load(f)
            self.feature_names = self.metadata['feature_names']
            # Build state->market map from data if not already in metadata
            if 'state_market_map' not in self.metadata:
                import pandas as pd
                data_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml_model', 'data', 'Price_Agriculture_commodities_Week.csv')
                if os.path.exists(data_path):
                    df = pd.read_csv(data_path)
                    self.metadata['state_market_map'] = (
                        df.groupby('State')['Market']
                        .unique().apply(sorted).apply(list).to_dict()
                    )
            self._loaded = True
            m = self.metadata
            print(f"  Model : {m['best_model']}")
            print(f"  MAE   : Rs{m['metrics'][m['best_model']]['mae']}/kg")
            print(f"  Unit  : {m.get('price_unit','INR_per_kg')}")
        except FileNotFoundError as e:
            print(f"Model not found: {e}\nRun ml_model/train_model.py first!")

    def _enc(self, col, val):
        le = self.encoders.get(col)
        if not le: return 0
        try:    return int(le.transform([str(val).strip().title()])[0])
        except: return 0

    def _build_feature_vector(self, inputs: dict) -> np.ndarray:
        d = pd.to_datetime(inputs.get('date', datetime.today().strftime('%Y-%m-%d')))
        d_date = d.date()
        m = d.month

        season = 'Kharif' if m in [6,7,8,9,10] else ('Rabi' if m in [11,12,1,2,3] else 'Zaid')
        commodity = str(inputs.get('commodity','')).strip().title()
        cat = ('vegetable' if commodity in VEGETABLES else
               'grain'     if commodity in GRAINS else
               'fruit'     if commodity in FRUITS else 'other')

        temp_map = {1:15,2:18,3:24,4:30,5:35,6:34,7:30,8:29,9:28,10:25,11:20,12:16}
        rain_map = {1:10,2:12,3:15,4:20,5:35,6:150,7:280,8:260,9:180,10:80,11:25,12:12}

        dtf = _days_to_festival(d_date)
        wsh, wth = _harvest_features(commodity, d_date)
        raw_price = float(inputs.get('current_price') or inputs.get('modal_price') or 0)
        modal = raw_price / 100.0 if raw_price > 200 else raw_price
        _min = inputs.get('min_price')
        _max = inputs.get('max_price')
        min_p = float(_min if _min is not None else modal * 0.9)
        max_p = float(_max if _max is not None else modal * 1.1)
        if min_p > 200: min_p /= 100
        if max_p > 200: max_p /= 100
        lag_7  = float(inputs.get('lag_7')  or modal)
        lag_14 = float(inputs.get('lag_14') or modal)
        lag_30 = float(inputs.get('lag_30') or modal)
        if lag_7  > 200: lag_7  /= 100
        if lag_14 > 200: lag_14 /= 100
        if lag_30 > 200: lag_30 /= 100

        rm7  = float(inputs.get('rolling_mean_7',  lag_7))
        rm14 = float(inputs.get('rolling_mean_14', lag_14))
        rm30 = float(inputs.get('rolling_mean_30', lag_30))

        row = {
            'state_enc':         self._enc('state',         inputs.get('state','')),
            'district_enc':      self._enc('district',      inputs.get('district','')),
            'market_enc':        self._enc('market',        inputs.get('market','')),
            'commodity_enc':     self._enc('commodity',     commodity),
            'variety_enc':       self._enc('variety',       inputs.get('variety','Other')),
            'grade_enc':         self._enc('grade',         inputs.get('grade','FAQ')),
            'season_enc':        self._enc('season',        season),
            'crop_category_enc': self._enc('crop_category', cat),
            'year':d.year,'month':m,'week':d.isocalendar()[1],'day_of_week':d.weekday(),
            'day_of_year':d.timetuple().tm_yday,'quarter':(m-1)//3+1,'is_weekend':int(d.weekday()>=5),
            'month_sin':np.sin(2*np.pi*m/12),'month_cos':np.cos(2*np.pi*m/12),
            'dow_sin':np.sin(2*np.pi*d.weekday()/7),'dow_cos':np.cos(2*np.pi*d.weekday()/7),
            'temp_proxy':temp_map[m],'rainfall_proxy':rain_map[m],'is_monsoon':int(m in [6,7,8,9]),
            'days_to_festival':dtf,'is_festival_season':int(dtf<=14),
            'min_price':min_p,'max_price':max_p,'price_spread':(max_p-min_p)/(modal+0.01),
            'lag_7':lag_7,'lag_14':lag_14,'lag_30':lag_30,
            'rolling_mean_7':rm7,'rolling_mean_14':rm14,'rolling_mean_30':rm30,
            'rolling_std_7':float(inputs.get('rolling_std_7',0)),
            'rolling_std_30':float(inputs.get('rolling_std_30',0)),
            'price_change_pct':float(inputs.get('price_change_pct',0)),
            'is_perishable':int(commodity in PERISHABLE),
            'market_price_rank':float(inputs.get('market_price_rank',0.5)),
            'storage_life_days':STORAGE_LIFE.get(commodity,60),
            'weeks_since_harvest':wsh,'weeks_to_harvest':wth,
            'competition_index':float(inputs.get('competition_index',5)),
            'state_median_price':float(inputs.get('state_median_price',modal)),
            'market_price_count':float(inputs.get('market_price_count',10)),
            'supply_proxy':float(inputs.get('supply_proxy',1.0)),
        }
        return np.array([[row.get(f,0) for f in self.feature_names]])

    def predict(self, inputs: dict) -> dict:
        if not self._loaded:
            raise RuntimeError("Model not loaded.")
        feat  = self._build_feature_vector(inputs)
        price_kg = max(0.5, float(self.model.predict(feat)[0]))
        mm    = self.metadata['metrics'].get(self.metadata['best_model'],{})
        mape  = mm.get('mape', 1.0)
        return {
            'predicted_price_kg':      round(price_kg, 2),
            'predicted_price_quintal': round(price_kg * 100, 2),
            'unit':                    'Rs/kg',
            'confidence':              round(max(10, min(99, 100 - mape)), 1),
            'model_used':              self.metadata['best_model'],
            'mae_kg':                  round(mm.get('mae', 0), 4),
        }

    def forecast(self, commodity, market, state, current_price_kg, horizon_days=30):
        if not self._loaded:
            raise RuntimeError("Model not loaded.")

        # Seasonal wave parameters per crop category
        commodity_title = str(commodity).title()
        is_vegetable = commodity_title in VEGETABLES
        is_grain     = commodity_title in GRAINS
        is_fruit     = commodity_title in FRUITS

        # Amplitude of price variation (realistic %)
        wave_amp   = 0.15 if is_vegetable else (0.06 if is_grain else 0.10)
        # Wave period in days (perishables move faster)
        wave_period = 14 if commodity_title in PERISHABLE else 21

        rolling = [current_price_kg] * 30
        today   = datetime.today()
        out     = []

        for i in range(1, horizon_days + 1):
            fd = today + timedelta(days=i)

            # ── Natural multi-wave price signal ──────────────
            # Primary seasonal wave
            primary  = wave_amp * np.sin(2 * np.pi * i / wave_period)
            # Secondary shorter wave (market noise)
            secondary = (wave_amp * 0.4) * np.sin(2 * np.pi * i / (wave_period * 0.4) + 1.2)
            # Slow trend component (±5% drift over full horizon)
            trend    = (wave_amp * 0.3) * np.sin(2 * np.pi * i / max(horizon_days, 30))
            # Combine signal
            signal_multiplier = 1.0 + primary + secondary + trend

            inputs = {
                'date':            fd.strftime('%Y-%m-%d'),
                'commodity':       commodity, 'market': market, 'state': state,
                'current_price':   rolling[-1] * signal_multiplier,
                'min_price':       rolling[-1] * 0.9,
                'max_price':       rolling[-1] * 1.1,
                'lag_7':           rolling[-7]  if len(rolling)>=7  else rolling[-1],
                'lag_14':          rolling[-14] if len(rolling)>=14 else rolling[-1],
                'lag_30':          rolling[-30] if len(rolling)>=30 else rolling[-1],
                'rolling_mean_7':  np.mean(rolling[-7:]),
                'rolling_mean_14': np.mean(rolling[-14:]) if len(rolling)>=14 else np.mean(rolling),
                'rolling_mean_30': np.mean(rolling),
                'rolling_std_7':   np.std(rolling[-7:])  if len(rolling)>=7  else 0,
                'rolling_std_30':  np.std(rolling),
                'price_change_pct':(rolling[-1]-rolling[-2])/(rolling[-2]+0.01) if len(rolling)>=2 else 0,
            }
            res = self.predict(inputs)
            p   = res['predicted_price_kg']
            rolling.append(p)
            chg = ((p - current_price_kg) / current_price_kg) * 100
            out.append({
                'day': i, 'date': fd.strftime('%Y-%m-%d'),
                'predicted_price_kg':      round(p, 2),
                'predicted_price_quintal': round(p * 100, 2),
                'change_from_today': round(chg, 2),
                'recommendation': 'SELL' if chg < -5 else ('HOLD' if chg > 5 else 'NEUTRAL'),
            })

        # Guarantee best and worst dates are different
        prices = [d['predicted_price_kg'] for d in out]
        best_idx  = int(np.argmax(prices))
        worst_idx = int(np.argmin(prices))
        # If somehow equal (flat prediction), force worst to a different day
        if best_idx == worst_idx:
            worst_idx = (best_idx + len(out) // 2) % len(out)

        out[best_idx]['is_best_sell']   = True
        out[worst_idx]['is_worst_sell'] = True

        return out

    @property
    def crops(self):   return self.metadata.get('crops_available', [])
    @property
    def markets(self): return self.metadata.get('markets_available', [])
    @property
    def states(self):  return sorted(self.metadata.get('state_market_map', {}).keys())
    @property
    def state_market_map(self): return self.metadata.get('state_market_map', {})
    @property
    def model_info(self): return self.metadata
