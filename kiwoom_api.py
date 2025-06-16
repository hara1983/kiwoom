import sys
import time
import pandas as pd
from PyQt5.QtWidgets import QApplication
from pykiwoom.kiwoom import Kiwoom
from datetime import datetime, timedelta
import numpy as np

class KiwoomAPI:
    def __init__(self):
        self.kiwoom = None
        self.app = None
        self.account = "7028-1544"  # 모의투자 계좌번호
        self.current_positions = {}
        self.order_history = []
        
    def connect(self):
        """키움 API 연결"""
        try:
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            
            self.kiwoom = Kiwoom()
            self.kiwoom.CommConnect()
            
            # 로그인 완료까지 대기
            while not self.kiwoom.get_connect_state():
                time.sleep(0.5)
                
            print("키움 API 연결 완료")
            return True
            
        except Exception as e:
            print(f"키움 API 연결 실패: {e}")
            return False
    
    def get_weekly_option_codes(self):
        """위클리 옵션 종목 코드 조회 (만기가 가장 짧은 것)"""
        try:
            # KOSPI200 옵션 종목 리스트 조회
            option_codes = self.kiwoom.get_code_list_by_market("301")  # 옵션 시장
            
            weekly_options = []
            current_date = datetime.now()
            
            for code in option_codes:
                # 종목명 조회
                code_name = self.kiwoom.get_master_code_name(code)
                
                # 위클리 옵션 판별 (W가 포함된 종목)
                if 'W' in code_name:
                    # 만료일 추출 (종목명에서)
                    try:
                        # 옵션 기본 정보 조회
                        option_info = self.get_option_info(code)
                        if option_info:
                            weekly_options.append(option_info)
                    except:
                        continue
            
            # 만기일 기준으로 정렬 (가장 짧은 것부터)
            weekly_options.sort(key=lambda x: x['expiry_date'])
            
            return weekly_options[:50]  # 상위 50개만 반환
            
        except Exception as e:
            print(f"위클리 옵션 조회 실패: {e}")
            return []
    
    def get_option_info(self, code):
        """옵션 종목 상세 정보 조회"""
        try:
            # 현재가 정보 조회
            current_price_data = self.kiwoom.get_opt10001(code)
            if not current_price_data:
                return None
                
            current_price = int(current_price_data['현재가'])
            
            # 가격이 0.1 이하인 종목 제외
            if current_price <= 100:  # 키움에서는 원단위이므로 100원 = 0.1원
                return None
            
            # 종목명에서 만료일과 행사가 추출
            code_name = self.kiwoom.get_master_code_name(code)
            
            option_info = {
                'code': code,
                'name': code_name,
                'current_price': current_price,
                'expiry_date': self.extract_expiry_date(code_name),
                'strike_price': self.extract_strike_price(code_name),
                'option_type': 'CALL' if 'C' in code_name else 'PUT'
            }
            
            return option_info
            
        except Exception as e:
            print(f"옵션 정보 조회 실패: {e}")
            return None
    
    def extract_expiry_date(self, code_name):
        """종목명에서 만료일 추출"""
        try:
            # 예: "K200 2412W4 270 C" -> 2024년 12월 4주차
            parts = code_name.split()
            for part in parts:
                if 'W' in part:
                    year_month = part[:4]
                    week = part[-1]
                    year = int('20' + year_month[:2])
                    month = int(year_month[2:])
                    
                    # 대략적인 만료일 계산 (정확한 계산은 더 복잡함)
                    week_num = int(week)
                    expiry_date = datetime(year, month, 1) + timedelta(weeks=week_num-1)
                    return expiry_date
        except:
            pass
        
        return datetime.now() + timedelta(days=7)  # 기본값
    
    def extract_strike_price(self, code_name):
        """종목명에서 행사가 추출"""
        try:
            parts = code_name.split()
            for part in parts:
                if part.isdigit():
                    return int(part) * 100  # 행사가는 보통 100배수
        except:
            pass
        return 0
    
    def select_trading_options(self, weekly_options):
        """거래할 옵션 선택 (가격 0.1~0.3 범위 우선)"""
        suitable_options = []
        
        for option in weekly_options:
            price = option['current_price']
            
            # 0.1~0.3 범위 (100원~300원)
            if 100 <= price <= 300:
                suitable_options.append(option)
        
        if suitable_options:
            return suitable_options[:10]  # 상위 10개
        
        # 적절한 옵션이 없으면 2외가, 3외가 옵션 선택
        # KOSPI200 현재가 조회
        kospi200_price = self.get_kospi200_current_price()
        
        otm_options = []
        for option in weekly_options:
            strike = option['strike_price']
            if option['option_type'] == 'CALL':
                # 콜옵션: 행사가가 현재가보다 높은 것 (OTM)
                if strike > kospi200_price:
                    otm_distance = strike - kospi200_price
                    if 200 <= otm_distance <= 600:  # 2~3외가 범위
                        otm_options.append(option)
            else:
                # 풋옵션: 행사가가 현재가보다 낮은 것 (OTM)
                if strike < kospi200_price:
                    otm_distance = kospi200_price - strike
                    if 200 <= otm_distance <= 600:  # 2~3외가 범위
                        otm_options.append(option)
        
        return otm_options[:10] if otm_options else weekly_options[:5]
    
    def get_kospi200_current_price(self):
        """KOSPI200 현재가 조회"""
        try:
            # KOSPI200 지수 코드
            kospi200_data = self.kiwoom.get_opt10001("101")
            if kospi200_data:
                return int(kospi200_data['현재가'])
        except:
            pass
        return 300  # 기본값
    
    def get_minute_data(self, code, count=200):
        """3분봉 데이터 조회"""
        try:
            # 분봉 데이터 조회 (틱범위: 3분)
            df = self.kiwoom.get_opt10080(code=code, 
                                        adjustment_price='1',  # 수정주가
                                        count=count,
                                        tick_range='3')  # 3분봉
            
            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                return df
            
        except Exception as e:
            print(f"분봉 데이터 조회 실패: {e}")
        
        return pd.DataFrame()
    
    def calculate_bollinger_bands(self, df, period=20, std_mult=2):
        """볼린저 밴드 계산"""
        if len(df) < period:
            return df
        
        df['MA'] = df['close'].rolling(window=period).mean()
        df['STD'] = df['close'].rolling(window=period).std()
        df['BB_Upper'] = df['MA'] + (df['STD'] * std_mult)
        df['BB_Lower'] = df['MA'] - (df['STD'] * std_mult)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        
        return df
    
    def calculate_ma_convergence(self, df, period1=5, period2=20, period3=60):
        """이동평균선 밀집도 계산"""
        if len(df) < period3:
            return df
        
        df['MA1'] = df['close'].rolling(window=period1).mean()
        df['MA2'] = df['close'].rolling(window=period2).mean()
        df['MA3'] = df['close'].rolling(window=period3).mean()
        
        # 세 이평선 중 최대값과 최소값
        df['MA_Max'] = df[['MA1', 'MA2', 'MA3']].max(axis=1)
        df['MA_Min'] = df[['MA1', 'MA2', 'MA3']].min(axis=1)
        df['MA_Convergence'] = df['MA_Max'] - df['MA_Min']
        
        return df
    
    def calculate_historical_bb_width(self, df, lookback_period=100):
        """절대 밴드폭 역사적 최저 계산"""
        if len(df) < lookback_period:
            return df
        
        df['Historical_Min_BB_Width'] = df['BB_Width'].rolling(
            window=lookback_period, min_periods=1).min()
        
        return df
    
    def send_order(self, code, order_type, quantity, price=0):
        """주문 전송"""
        try:
            # 주문 타입: 1-신규매수, 2-신규매도, 3-매수취소, 4-매도취소, 5-매수정정, 6-매도정정
            order_type_code = "1" if order_type == "BUY" else "2"
            
            # 시장가 주문이면 가격을 0으로
            if price == 0:
                hoga_gubun = "03"  # 시장가
            else:
                hoga_gubun = "00"  # 지정가
            
            result = self.kiwoom.send_order(
                "AUTO_ORDER",  # 사용자구분명
                "0101",        # 화면번호
                self.account,  # 계좌번호
                order_type_code,  # 주문유형
                code,          # 종목코드
                quantity,      # 주문수량
                price,         # 주문가격
                hoga_gubun,    # 호가구분
                ""             # 원주문번호
            )
            
            if result == 0:
                print(f"주문 전송 성공: {code}, {order_type}, {quantity}주, {price}원")
                return True
            else:
                print(f"주문 전송 실패: {result}")
                return False
                
        except Exception as e:
            print(f"주문 전송 중 오류: {e}")
            return False
    
    def get_current_price(self, code):
        """현재가 조회"""
        try:
            data = self.kiwoom.get_opt10001(code)
            if data:
                return int(data['현재가'])
        except:
            pass
        return 0
    
    def get_bid_ask_price(self, code):
        """호가 정보 조회"""
        try:
            # 호가 정보 조회
            hoga_data = self.kiwoom.get_opt10004(code)
            if hoga_data:
                bid_price = int(hoga_data.get('매수최우선호가', 0))
                ask_price = int(hoga_data.get('매도최우선호가', 0))
                return bid_price, ask_price
        except:
            pass
        return 0, 0
    
    def smart_order(self, code, order_type, quantity, max_attempts=5):
        """스마트 주문 (스프레드 고려하여 단계적으로 호가 조정)"""
        current_price = self.get_current_price(code)
        bid_price, ask_price = self.get_bid_ask_price(code)
        
        if order_type == "BUY":
            # 매수: 매도호가부터 시작해서 단계적으로 올림
            base_price = ask_price if ask_price > 0 else current_price
        else:
            # 매도: 매수호가부터 시작해서 단계적으로 내림
            base_price = bid_price if bid_price > 0 else current_price
        
        for attempt in range(max_attempts):
            if order_type == "BUY":
                order_price = base_price + (attempt * 5)  # 5원씩 올림
            else:
                order_price = base_price - (attempt * 5)  # 5원씩 내림
            
            print(f"주문 시도 {attempt+1}: {code}, {order_type}, {order_price}원")
            
            if self.send_order(code, order_type, quantity, order_price):
                # 잠시 대기 후 체결 확인
                time.sleep(2)
                
                # 체결 확인 로직 (실제로는 체결 이벤트를 받아야 함)
                # 여기서는 간단히 처리
                return True
        
        print(f"주문 실패: {code}, 최대 시도 횟수 초과")
        return False
    
    def get_balance(self):
        """잔고 조회"""
        try:
            balance_data = self.kiwoom.get_opt10075(self.account, "")
            return balance_data
        except Exception as e:
            print(f"잔고 조회 실패: {e}")
            return {}
    
    def disconnect(self):
        """연결 해제"""
        if self.kiwoom:
            self.kiwoom.CommTerminate()
        if self.app:
            self.app.quit()