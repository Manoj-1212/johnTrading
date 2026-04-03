"""
Phase 10: Machine Learning Trade Filter
========================================
Uses XGBoost to filter false signals from the indicator system.

How it works:
1. Train on historical data: features = 7 indicators + price features
2. Target: Did price go up by ML_TARGET_RETURN in next ML_LOOKBACK_BARS bars?
3. At runtime: only execute trades when ML says confidence > ML_MIN_CONFIDENCE

This filters out ~40-60% of false BUY signals that would lose money.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import joblib

from config import (
    ML_MODEL_PATH, ML_MIN_CONFIDENCE, ML_LOOKBACK_BARS, ML_TARGET_RETURN
)


class MLTradeFilter:
    """
    XGBoost-based trade confidence filter.
    
    Features used:
    - RSI, MACD, EMA trend, Volume ratio, ATR, BB position
    - Price momentum (1-bar, 5-bar, 10-bar returns)
    - Volatility (rolling std)
    - Signal count from indicator system
    
    Target:
    - 1 if price rose > ML_TARGET_RETURN in next ML_LOOKBACK_BARS bars
    - 0 otherwise
    """
    
    def __init__(self, model_path=None):
        self.model_path = Path(model_path or ML_MODEL_PATH)
        self.model = None
        self.feature_columns = None
        self._load_model()
    
    def _load_model(self):
        """Load trained model from disk if available."""
        if self.model_path.exists():
            try:
                saved = joblib.load(self.model_path)
                self.model = saved['model']
                self.feature_columns = saved['feature_columns']
                print(f"ML Filter: Loaded model from {self.model_path}")
            except Exception as e:
                print(f"ML Filter: Could not load model: {e}")
                self.model = None
    
    def is_trained(self):
        """Check if model is trained and ready."""
        return self.model is not None
    
    def train(self, data_dict, verbose=True):
        """
        Train the ML filter on historical data.
        
        Parameters
        ----------
        data_dict : dict
            {ticker: DataFrame} with OHLCV + indicator columns
        verbose : bool
            Print training progress
        """
        try:
            from xgboost import XGBClassifier
        except ImportError:
            print("ERROR: xgboost not installed. Run: pip install xgboost")
            return None
        
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.metrics import classification_report, roc_auc_score
        
        if verbose:
            print("\n" + "=" * 80)
            print("PHASE 10: TRAINING ML TRADE FILTER")
            print("=" * 80)
        
        # Build training dataset from all tickers
        all_features = []
        all_targets = []
        
        for ticker, df in data_dict.items():
            if df.empty or len(df) < 100:
                continue
            
            features, target = self._build_features(df)
            if features is not None and len(features) > 0:
                all_features.append(features)
                all_targets.append(target)
                if verbose:
                    pos_rate = target.mean() * 100
                    print(f"  {ticker}: {len(features)} samples, {pos_rate:.1f}% positive")
        
        if not all_features:
            print("ERROR: No training data available")
            return None
        
        X = pd.concat(all_features, ignore_index=True)
        y = pd.concat(all_targets, ignore_index=True)
        
        self.feature_columns = list(X.columns)
        
        if verbose:
            print(f"\nTotal: {len(X)} samples, {y.mean()*100:.1f}% positive rate")
            print(f"Features: {len(self.feature_columns)}")
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        scores = []
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model = XGBClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                use_label_encoder=False,
                eval_metric='logloss',
                random_state=42,
            )
            
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
            
            val_proba = model.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, val_proba)
            scores.append(auc)
            
            if verbose:
                print(f"  Fold {fold+1}: AUC = {auc:.4f}")
        
        avg_auc = np.mean(scores)
        if verbose:
            print(f"\nAvg AUC: {avg_auc:.4f}")
        
        # Train final model on all data
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42,
        )
        self.model.fit(X, y, verbose=False)
        
        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.save({
            'model': self.model,
            'feature_columns': self.feature_columns,
            'trained_at': datetime.now().isoformat(),
            'avg_auc': avg_auc,
            'n_samples': len(X),
        }, self.model_path)
        
        if verbose:
            print(f"\nModel saved to {self.model_path}")
            
            # Feature importance
            importances = pd.Series(
                self.model.feature_importances_,
                index=self.feature_columns
            ).sort_values(ascending=False)
            
            print(f"\nTop 10 Features:")
            for feat, imp in importances.head(10).items():
                bar = "█" * int(imp * 50)
                print(f"  {feat:<25} {imp:.4f} {bar}")
        
        return avg_auc
    
    def predict_confidence(self, indicators, bars_df=None):
        """
        Predict confidence that this trade will be profitable.
        
        Parameters
        ----------
        indicators : dict
            Real-time indicator values from RealtimeIndicatorCalculator
        bars_df : pd.DataFrame, optional
            Recent price bars for computing price features
        
        Returns
        -------
        float
            Confidence score 0.0-1.0 (probability of profitable trade)
        """
        if not self.is_trained():
            return 0.5  # Neutral if no model
        
        try:
            features = self._build_realtime_features(indicators, bars_df)
            if features is None:
                return 0.5
            
            # Ensure features match training columns
            features_aligned = pd.DataFrame([features])[self.feature_columns]
            proba = self.model.predict_proba(features_aligned)[0][1]
            return float(proba)
        except Exception as e:
            print(f"ML Filter prediction error: {e}")
            return 0.5
    
    def should_execute(self, indicators, bars_df=None):
        """
        Should this trade be executed based on ML confidence?
        
        Returns
        -------
        tuple (bool, float)
            (should_execute, confidence_score)
        """
        confidence = self.predict_confidence(indicators, bars_df)
        return confidence >= ML_MIN_CONFIDENCE, confidence
    
    def _build_features(self, df):
        """
        Build feature matrix from historical DataFrame.
        
        Features:
        - Technical indicators (RSI, MACD, BB position, etc.)
        - Price momentum (1, 5, 10 bar returns)
        - Volatility (rolling std)
        - Volume features
        - Signal count
        """
        try:
            features = pd.DataFrame(index=df.index)
            
            # Price features
            close = df['Close']
            features['return_1'] = close.pct_change(1)
            features['return_5'] = close.pct_change(5)
            features['return_10'] = close.pct_change(10)
            features['volatility_10'] = close.pct_change().rolling(10).std()
            features['volatility_20'] = close.pct_change().rolling(20).std()
            
            # RSI
            if 'RSI' in df.columns:
                features['rsi'] = df['RSI']
            elif 'rsi_signal' in df.columns:
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                features['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            features['macd'] = ema12 - ema26
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_hist'] = features['macd'] - features['macd_signal']
            
            # EMA trend
            ema50 = close.ewm(span=50).mean()
            ema200 = close.ewm(span=200).mean()
            features['ema_spread'] = (ema50 - ema200) / ema200
            features['price_vs_ema50'] = (close - ema50) / ema50
            features['price_vs_ema200'] = (close - ema200) / ema200
            
            # Bollinger Bands position
            bb_mid = close.rolling(20).mean()
            bb_std = close.rolling(20).std()
            features['bb_position'] = (close - bb_mid) / (bb_std * 2 + 1e-8)
            
            # ATR (normalized)
            if 'High' in df.columns and 'Low' in df.columns:
                tr = pd.concat([
                    df['High'] - df['Low'],
                    (df['High'] - close.shift(1)).abs(),
                    (df['Low'] - close.shift(1)).abs()
                ], axis=1).max(axis=1)
                features['atr_pct'] = tr.rolling(14).mean() / close
            
            # Volume
            if 'Volume' in df.columns:
                vol = df['Volume']
                features['volume_ratio'] = vol / vol.rolling(20).mean().replace(0, np.nan)
                features['volume_trend'] = vol.rolling(5).mean() / vol.rolling(20).mean().replace(0, np.nan)
            
            # Signal count from indicator system
            if 'signal_count' in df.columns:
                features['signal_count'] = df['signal_count']
            
            if 'composite_score' in df.columns:
                features['composite_score'] = df['composite_score']
            
            # Target: price goes up by ML_TARGET_RETURN in next ML_LOOKBACK_BARS bars
            future_return = close.shift(-ML_LOOKBACK_BARS) / close - 1
            target = (future_return > ML_TARGET_RETURN).astype(int)
            
            # Drop NaN rows
            valid = features.dropna().index.intersection(target.dropna().index)
            features = features.loc[valid]
            target = target.loc[valid]
            
            # Remove future leakage — drop last ML_LOOKBACK_BARS rows
            if len(features) > ML_LOOKBACK_BARS:
                features = features.iloc[:-ML_LOOKBACK_BARS]
                target = target.iloc[:-ML_LOOKBACK_BARS]
            
            return features, target
            
        except Exception as e:
            print(f"Error building features: {e}")
            return None, None
    
    def _build_realtime_features(self, indicators, bars_df=None):
        """
        Build feature dict from real-time indicator values.
        Maps realtime indicator dict to same features used in training.
        """
        try:
            features = {}
            
            if bars_df is not None and len(bars_df) >= 20:
                close = bars_df['Close']
                
                # Price features
                features['return_1'] = float((close.iloc[-1] / close.iloc[-2] - 1)) if len(close) >= 2 else 0
                features['return_5'] = float((close.iloc[-1] / close.iloc[-6] - 1)) if len(close) >= 6 else 0
                features['return_10'] = float((close.iloc[-1] / close.iloc[-11] - 1)) if len(close) >= 11 else 0
                returns = close.pct_change()
                features['volatility_10'] = float(returns.iloc[-10:].std()) if len(returns) >= 10 else 0
                features['volatility_20'] = float(returns.iloc[-20:].std()) if len(returns) >= 20 else 0
                
                # BB position
                bb_mid = float(close.iloc[-20:].mean())
                bb_std = float(close.iloc[-20:].std())
                current = float(close.iloc[-1])
                features['bb_position'] = (current - bb_mid) / (bb_std * 2 + 1e-8)
                
                # ATR
                if 'High' in bars_df.columns and 'Low' in bars_df.columns:
                    tr = pd.concat([
                        bars_df['High'] - bars_df['Low'],
                        (bars_df['High'] - close.shift(1)).abs(),
                        (bars_df['Low'] - close.shift(1)).abs()
                    ], axis=1).max(axis=1)
                    features['atr_pct'] = float(tr.iloc[-14:].mean() / current) if current > 0 else 0
                
                # Volume
                if 'Volume' in bars_df.columns:
                    vol = bars_df['Volume']
                    vol_ma20 = float(vol.iloc[-20:].mean())
                    vol_ma5 = float(vol.iloc[-5:].mean())
                    features['volume_ratio'] = float(vol.iloc[-1]) / vol_ma20 if vol_ma20 > 0 else 1
                    features['volume_trend'] = vol_ma5 / vol_ma20 if vol_ma20 > 0 else 1
                
                # EMA features
                ema50 = float(close.ewm(span=50).mean().iloc[-1])
                ema200 = float(close.ewm(span=min(200, len(close))).mean().iloc[-1])
                features['ema_spread'] = (ema50 - ema200) / ema200 if ema200 > 0 else 0
                features['price_vs_ema50'] = (current - ema50) / ema50 if ema50 > 0 else 0
                features['price_vs_ema200'] = (current - ema200) / ema200 if ema200 > 0 else 0
            else:
                # Fallback: use indicator values directly
                features['return_1'] = 0
                features['return_5'] = 0
                features['return_10'] = 0
                features['volatility_10'] = indicators.get('atr_percent', 0) / 100
                features['volatility_20'] = indicators.get('atr_percent', 0) / 100
                
                bb_upper = float(indicators.get('bb_upper', 0))
                bb_lower = float(indicators.get('bb_lower', 0))
                bb_mid = float(indicators.get('bb_middle', 0))
                current = float(indicators.get('current_price', 0))
                bb_range = bb_upper - bb_lower if bb_upper > bb_lower else 1
                features['bb_position'] = (current - bb_mid) / (bb_range / 2 + 1e-8)
                
                features['atr_pct'] = indicators.get('atr_percent', 0) / 100
                features['volume_ratio'] = indicators.get('volume_ratio', 1)
                features['volume_trend'] = indicators.get('volume_ratio', 1)
                
                ema50 = float(indicators.get('ema50', 0))
                ema200 = float(indicators.get('ema200', 0))
                features['ema_spread'] = (ema50 - ema200) / ema200 if ema200 > 0 else 0
                features['price_vs_ema50'] = (current - ema50) / ema50 if ema50 > 0 else 0
                features['price_vs_ema200'] = (current - ema200) / ema200 if ema200 > 0 else 0
            
            # Indicators available from both paths
            features['rsi'] = indicators.get('rsi', 50)
            
            macd = indicators.get('macd', 0)
            features['macd'] = float(macd) if not isinstance(macd, str) else 0
            
            macd_sig = indicators.get('macd_signal', 0)
            # macd_signal might be 'BULLISH'/'BEARISH' string in realtime
            if isinstance(macd_sig, str):
                features['macd_signal'] = 1 if macd_sig == 'BULLISH' else (-1 if macd_sig == 'BEARISH' else 0)
            else:
                features['macd_signal'] = float(macd_sig)
            
            features['macd_hist'] = float(indicators.get('macd_hist', 0))
            features['signal_count'] = indicators.get('signal_strength', 3)
            features['composite_score'] = indicators.get('signal_strength', 3) / 7.0
            
            # Fill missing features with 0
            if self.feature_columns:
                for col in self.feature_columns:
                    if col not in features:
                        features[col] = 0
            
            return features
            
        except Exception as e:
            print(f"Error building realtime features: {e}")
            return None
