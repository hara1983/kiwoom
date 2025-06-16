#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
from PyQt5.QtWidgets import QApplication

# 프로젝트 모듈 import
from kiwoom_api import KiwoomAPI
from config import Config
from strategy import OptionTradingStrategy
from logger import TradingLogger

class AutoTrader:
    def __init__(self):
        self.config = Config()
        self.logger = TradingLogger()
        self.kiwoom = KiwoomAPI()
        self.strategy = OptionTradingStrategy(self.kiwoom, self.logger)
        
        self.is_running = False
        self.selected_options = []
        self.positions = {}  # {종목코드: {'quantity': 수량, 'entry_price': 진입가, 'entry_time': 진입시간}}
        
        # 거래 시간 설정
        self.market_open_time = "09:00"
        self.market_close_time = "15:20"
        
    def initialize(self):
        """시스템 초기화"""
        try:
            self.logger.info("=== 자동매매 시스템 시작 ===")
            
            # 키움 API 연결
            if not self.kiwoom.connect():
                self.logger.error("키움 API 연결 실패")
                return False
            
            self.logger.info("키움 API 연결 성공")
            
            # 위클리 옵션 종목 선정
            self.select_trading_options()
            
            return True
            
        except Exception as e:
            self.logger.error(f"초기화 중 오류 발생: {e}")
            return False
    
    def select_trading_options(self):
        """거래할 위클리 옵션 선정"""
        try:
            self.logger.info("위클리 옵션 종목 선정 시작")
            
            # 위클리 옵션 전체 조회
            weekly_options = self.kiwoom.get_weekly_option_codes()
            
            if not weekly_options:
                self.logger.warning("위클리 옵션을 찾을 수 없습니다")
                return
            
            # 거래 조건에 맞는 옵션 선택
            self.selected_options = self.kiwoom.select_trading_options(weekly_options)
            
            self.logger.info(f"선정된 옵션 종목 수: {len(self.selected_options)}")
            
            for option in self.selected_options:
                self.logger.info(f"선정 종목: {option['name']} ({option['code']}) - "
                               f"현재가: {option['current_price']}원")
                
        except Exception as e:
            self.logger.error(f"옵션 종목 선정 중 오류: {e}")
    
    def is_market_open(self):
        """장중 시간 확인"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 주말 제외
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 장중 시간 확인
        return self.market_open_time <= current_time <= self.market_close_time
    
    def check_buy_signals(self):
        """매수 신호 확인"""
        if not self.selected_options:
            return
        
        for option in self.selected_options:
            code = option['code']
            
            # 이미 보유 중인 종목은 스킵
            if code in self.positions:
                continue
            
            try:
                # 3분봉 데이터 조회
                df = self.kiwoom.get_minute_data(code, count=200)
                
                if df.empty or len(df) < 100:
                    continue
                
                # 기술적 지표 계산
                df = self.kiwoom.calculate_bollinger_bands(df)
                df = self.kiwoom.calculate_ma_convergence(df)
                df = self.kiwoom.calculate_historical_bb_width(df)
                
                # 매수 신호 확인
                if self.strategy.check_buy_signal(df):
                    self.execute_buy_order(option)
                    
            except Exception as e:
                self.logger.error(f"매수 신호 확인 중 오류 ({code}): {e}")
    
    def execute_buy_order(self, option):
        """매수 주문 실행"""
        try:
            code = option['code']
            name = option['name']
            
            # 매수 수량 계산 (총 투자금액의 일정 비율)
            quantity = self.calculate_order_quantity(option['current_price'])
            
            self.logger.info(f"매수 신호 발생: {name} ({code}) - {quantity}주 매수 시도")
            
            # 스마트 주문 실행
            if self.kiwoom.smart_order(code, "BUY", quantity):
                # 포지션 기록
                self.positions[code] = {
                    'name': name,
                    'quantity': quantity,
                    'entry_price': option['current_price'],
                    'entry_time': datetime.now(),
                    'option_info': option
                }
                
                self.logger.info(f"매수 완료: {name} ({code}) - {quantity}주")
                
            else:
                self.logger.warning(f"매수 실패: {name} ({code})")
                
        except Exception as e:
            self.logger.error(f"매수 주문 실행 중 오류: {e}")
    
    def calculate_order_quantity(self, price):
        """주문 수량 계산"""
        try:
            # 계좌 잔고 조회
            balance_info = self.kiwoom.get_balance()
            
            # 사용 가능한 금액 계산 (예: 총 자산의 10%)
            available_cash = self.config.MAX_INVESTMENT_PER_TRADE
            
            # 수량 계산 (최소 1주, 최대 설정값)
            quantity = max(1, min(available_cash // price, self.config.MAX_QUANTITY_PER_TRADE))
            
            return quantity
            
        except Exception as e:
            self.logger.error(f"주문 수량 계산 중 오류: {e}")
            return 1  # 기본값
    
    def check_sell_signals(self):
        """매도 신호 확인 (보유 포지션 대상)"""
        positions_to_close = []
        
        for code, position in self.positions.items():
            try:
                # 현재가 조회
                current_price = self.kiwoom.get_current_price(code)
                
                if current_price == 0:
                    continue
                
                # 3분봉 데이터 조회
                df = self.kiwoom.get_minute_data(code, count=50)
                
                if df.empty or len(df) < 10:
                    continue
                
                # 10개봉 이동평균 계산
                df['MA10'] = df['close'].rolling(window=10).mean()
                latest_ma10 = df['MA10'].iloc[-1]
                latest_close = df['close'].iloc[-1]
                
                # 매도 조건 확인
                should_sell = False
                sell_reason = ""
                
                # 1. 10개봉 이동평균선 이하로 종가가 내려온 경우
                if latest_close < latest_ma10:
                    should_sell = True
                    sell_reason = "10개봉 이평선 하향 이탈"
                
                # 2. 10% 손실 시 손절
                entry_price = position['entry_price']
                loss_pct = (entry_price - current_price) / entry_price * 100
                
                if loss_pct >= self.config.STOP_LOSS_PCT:
                    should_sell = True
                    sell_reason = f"손절 ({loss_pct:.1f}% 손실)"
                
                # 매도 실행
                if should_sell:
                    self.execute_sell_order(code, position, sell_reason)
                    positions_to_close.append(code)
                    
            except Exception as e:
                self.logger.error(f"매도 신호 확인 중 오류 ({code}): {e}")
        
        # 매도 완료된 포지션 제거
        for code in positions_to_close:
            del self.positions[code]
    
    def execute_sell_order(self, code, position, reason):
        """매도 주문 실행"""
        try:
            name = position['name']
            quantity = position['quantity']
            
            self.logger.info(f"매도 신호 발생: {name} ({code}) - {reason}")
            
            # 스마트 주문 실행
            if self.kiwoom.smart_order(code, "SELL", quantity):
                # 수익/손실 계산
                current_price = self.kiwoom.get_current_price(code)
                entry_price = position['entry_price']
                pnl = (current_price - entry_price) * quantity
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                self.logger.info(f"매도 완료: {name} ({code}) - {quantity}주")
                self.logger.info(f"매매결과: {pnl:+,}원 ({pnl_pct:+.1f}%)")
                
            else:
                self.logger.warning(f"매도 실패: {name} ({code})")
                
        except Exception as e:
            self.logger.error(f"매도 주문 실행 중 오류: {e}")
    
    def monitor_positions(self):
        """포지션 모니터링"""
        if self.positions:
            self.logger.info(f"현재 보유 포지션: {len(self.positions)}개")
            
            for code, position in self.positions.items():
                current_price = self.kiwoom.get_current_price(code)
                if current_price > 0:
                    entry_price = position['entry_price']
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    
                    self.logger.info(f"  {position['name']}: {pnl_pct:+.1f}% "
                                   f"({entry_price}→{current_price})")
    
    def trading_loop(self):
        """메인 거래 루프"""
        self.logger.info("거래 루프 시작")
        
        while self.is_running:
            try:
                # 장중 시간 확인
                if not self.is_market_open():
                    self.logger.info("장외 시간 - 대기 중...")
                    time.sleep(60)  # 1분 대기
                    continue
                
                # 매수 신호 확인
                self.check_buy_signals()
                
                # 매도 신호 확인
                self.check_sell_signals()
                
                # 포지션 모니터링
                self.monitor_positions()
                
                # 3분 대기 (3분봉 기준)
                time.sleep(180)
                
            except KeyboardInterrupt:
                self.logger.info("사용자에 의한 종료 요청")
                break
            except Exception as e:
                self.logger.error(f"거래 루프 중 오류: {e}")
                time.sleep(30)  # 30초 대기 후 재시도
        
        self.logger.info("거래 루프 종료")
    
    def start(self):
        """자동매매 시작"""
        try:
            if not self.initialize():
                return False
            
            self.is_running = True
            
            # 별도 스레드에서 거래 루프 실행
            trading_thread = threading.Thread(target=self.trading_loop)
            trading_thread.daemon = True
            trading_thread.start()
            
            self.logger.info("자동매매 시작됨")
            
            # 메인 스레드에서 Qt 이벤트 루프 실행
            if QApplication.instance():
                QApplication.instance().exec_()
            
            return True
            
        except Exception as e:
            self.logger.error(f"자동매매 시작 중 오류: {e}")
            return False
    
    def stop(self):
        """자동매매 중지"""
        self.is_running = False
        self.logger.info("자동매매 중지됨")
        
        # API 연결 해제
        self.kiwoom.disconnect()

def main():
    """메인 함수"""
    print("KIWOOM 위클리 옵션 자동매매 시스템")
    print("=" * 50)
    
    # 자동매매 시스템 생성
    trader = AutoTrader()
    
    try:
        # 시스템 시작
        trader.start()
        
    except KeyboardInterrupt:
        print("\n사용자에 의한 종료...")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        # 시스템 정리
        trader.stop()
        print("시스템 종료 완료")

if __name__ == "__main__":
    main()