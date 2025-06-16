import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

class OptionTradingStrategy:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 전략 파라미터
        self.ma_convergence_params = {
            'period1': 5,    # 단기 이동평균
            'period2': 20,   # 중기 이동평균
            'period3': 60,   # 장기 이동평균
        }
        
        self.bollinger_params = {
            'period': 20,           # 볼린저밴드 기간
            'mult': 2,              # 표준편차 승수
            'lookback_period': 100  # 역사적 최저 밴드폭 비교 기간
        }
        
        # 매매 관련 파라미터
        self.exit_ma_period = 10    # 청산용 이동평균 기간
        self.stop_loss_rate = 0.10  # 10% 손절
        self.price_range = (0.1, 0.3)  # 거래 대상 옵션 가격 범위
        
        # 상태 변수
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        self.price_data = pd.DataFrame()
        
    def update_price_data(self, price_data):
        """가격 데이터 업데이트 (3분봉)"""
        self.price_data = price_data
        
    def calculate_ma_convergence(self, prices):
        """이동평균선 밀집도 계산"""
        if len(prices) < self.ma_convergence_params['period3']:
            return None, None, None, None
            
        # 각 기간별 이동평균 계산
        ma1 = prices.rolling(window=self.ma_convergence_params['period1']).mean()
        ma2 = prices.rolling(window=self.ma_convergence_params['period2']).mean()
        ma3 = prices.rolling(window=self.ma_convergence_params['period3']).mean()
        
        # 최대값, 최소값 계산
        max_ma = np.maximum(ma1, np.maximum(ma2, ma3))
        min_ma = np.minimum(ma1, np.minimum(ma2, ma3))
        
        # 밀집도 계산 (최대값 - 최소값)
        convergence_value = max_ma - min_ma
        
        return ma1, ma2, ma3, convergence_value
    
    def calculate_bollinger_bands(self, prices):
        """볼린저밴드 및 절대 밴드폭 계산"""
        if len(prices) < self.bollinger_params['period']:
            return None, None, None, None
            
        # 볼린저밴드 계산
        sma = prices.rolling(window=self.bollinger_params['period']).mean()
        std = prices.rolling(window=self.bollinger_params['period']).std()
        
        upper_band = sma + (std * self.bollinger_params['mult'])
        lower_band = sma - (std * self.bollinger_params['mult'])
        
        # 현재 절대 밴드폭
        current_bandwidth = upper_band - lower_band
        
        # 과거 기간 중 최저 밴드폭
        if len(current_bandwidth) >= self.bollinger_params['lookback_period']:
            historical_lowest = current_bandwidth.rolling(
                window=self.bollinger_params['lookback_period']
            ).min()
        else:
            historical_lowest = None
            
        return upper_band, lower_band, current_bandwidth, historical_lowest
    
    def check_buy_conditions(self):
        """매수 조건 확인"""
        if len(self.price_data) < max(self.ma_convergence_params['period3'], 
                                     self.bollinger_params['lookback_period']):
            return False
            
        prices = self.price_data['close']
        
        # 1. 이동평균선 밀집도 계산
        ma1, ma2, ma3, convergence = self.calculate_ma_convergence(prices)
        if convergence is None:
            return False
            
        # 2. 볼린저밴드 및 밴드폭 계산
        upper_b, lower_b, current_bw, historical_lowest_bw = self.calculate_bollinger_bands(prices)
        if current_bw is None or historical_lowest_bw is None:
            return False
            
        # 현재 값들
        current_convergence = convergence.iloc[-1]
        current_bandwidth = current_bw.iloc[-1]
        historical_min_bandwidth = historical_lowest_bw.iloc[-1]
        
        # 매수 조건 확인
        # 조건 1: 이동평균선 밀집도가 낮을 때 (임계값은 현재가의 1%로 설정)
        current_price = prices.iloc[-1]
        convergence_threshold = current_price * 0.01
        
        condition1 = current_convergence <= convergence_threshold
        
        # 조건 2: 현재 밴드폭이 역사적 최저 근처일 때 (110% 이내)
        condition2 = current_bandwidth <= (historical_min_bandwidth * 1.10)
        
        self.logger.info(f"매수 조건 확인 - 밀집도: {current_convergence:.4f} (임계값: {convergence_threshold:.4f}), "
                        f"현재 밴드폭: {current_bandwidth:.4f}, 역사적 최저: {historical_min_bandwidth:.4f}")
        
        return condition1 and condition2
    
    def check_sell_conditions(self):
        """매도 조건 확인"""
        if self.position is None:
            return False, "포지션 없음"
            
        if len(self.price_data) < self.exit_ma_period:
            return False, "데이터 부족"
            
        current_price = self.price_data['close'].iloc[-1]
        
        # 조건 1: 10% 손절
        loss_rate = (self.entry_price - current_price) / self.entry_price
        if loss_rate >= self.stop_loss_rate:
            return True, f"손절 - 손실률: {loss_rate:.2%}"
        
        # 조건 2: 10봉 이동평균 하향 돌파
        exit_ma = self.price_data['close'].rolling(window=self.exit_ma_period).mean()
        current_ma = exit_ma.iloc[-1]
        
        if current_price < current_ma:
            profit_rate = (current_price - self.entry_price) / self.entry_price
            return True, f"이평선 하향돌파 - 수익률: {profit_rate:.2%}"
        
        return False, "매도 조건 미충족"
    
    def is_valid_option_price(self, price):
        """옵션 가격이 거래 범위 내인지 확인"""
        return self.price_range[0] <= price <= self.price_range[1]
    
    def enter_position(self, option_code, current_price):
        """포지션 진입"""
        if not self.is_valid_option_price(current_price):
            self.logger.warning(f"옵션 가격 {current_price}이 거래 범위 {self.price_range} 밖임")
            return False
            
        self.position = {
            'code': option_code,
            'entry_price': current_price,
            'entry_time': datetime.now(),
            'quantity': 1  # 기본 수량
        }
        
        self.entry_price = current_price
        self.entry_time = datetime.now()
        
        self.logger.info(f"포지션 진입 - 종목: {option_code}, 가격: {current_price}")
        return True
    
    def exit_position(self, reason=""):
        """포지션 청산"""
        if self.position is None:
            return False
            
        current_price = self.price_data['close'].iloc[-1]
        profit_loss = current_price - self.entry_price
        profit_rate = profit_loss / self.entry_price
        
        self.logger.info(f"포지션 청산 - 종목: {self.position['code']}, "
                        f"진입가: {self.entry_price}, 청산가: {current_price}, "
                        f"손익: {profit_loss:.2f} ({profit_rate:.2%}), 사유: {reason}")
        
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        
        return True
    
    def get_signal(self):
        """매매 신호 생성"""
        if self.position is None:
            # 포지션 없을 때 - 매수 신호 확인
            if self.check_buy_conditions():
                return "BUY"
        else:
            # 포지션 있을 때 - 매도 신호 확인
            should_sell, reason = self.check_sell_conditions()
            if should_sell:
                return "SELL", reason
                
        return "HOLD"
    
    def calculate_order_price(self, current_price, order_type, spread_info=None):
        """주문 가격 계산 (스프레드 고려)"""
        if spread_info is None:
            # 스프레드 정보가 없으면 현재가로 주문
            return current_price
            
        bid_price = spread_info.get('bid_price', current_price)
        ask_price = spread_info.get('ask_price', current_price)
        spread = ask_price - bid_price
        
        # 스프레드가 과도하게 큰 경우 (현재가의 5% 이상)
        if spread > current_price * 0.05:
            if order_type == "BUY":
                # 매수 시 매도호가에서 한 단계 내려서 주문
                return max(bid_price, ask_price - 0.01)
            else:  # SELL
                # 매도 시 매수호가에서 한 단계 올려서 주문
                return min(ask_price, bid_price + 0.01)
        else:
            # 스프레드가 적당하면 현재가로 주문
            return current_price
    
    def get_strategy_status(self):
        """전략 상태 반환"""
        status = {
            'position': self.position,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time,
            'data_length': len(self.price_data) if not self.price_data.empty else 0
        }
        
        if self.position and not self.price_data.empty:
            current_price = self.price_data['close'].iloc[-1]
            unrealized_pnl = current_price - self.entry_price
            unrealized_rate = unrealized_pnl / self.entry_price
            status['unrealized_pnl'] = unrealized_pnl
            status['unrealized_rate'] = unrealized_rate
            
        return status