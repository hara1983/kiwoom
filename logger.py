# logger.py - 키움증권 API 시스템 트레이딩 로그 시스템
# ============================================================================

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
from config import Config

class TradingLogger:
    """키움증권 시스템 트레이딩 전용 로거"""
    
    def __init__(self, name: str = "KiwoomTrading"):
        self.name = name
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """로거 초기 설정"""
        # 로거 생성
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, Config.LOGGING['log_level']))
        
        # 중복 핸들러 방지
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 포매터 설정
        formatter = self._create_formatter()
        
        # 파일 핸들러 추가
        self._add_file_handler(formatter)
        
        # 콘솔 핸들러 추가
        if Config.LOGGING.get('console_output', True):
            self._add_console_handler(formatter)
        
        # 거래 전용 파일 핸들러 추가
        self._add_trading_handler(formatter)
    
    def _create_formatter(self):
        """로그 포매터 생성"""
        return logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _add_file_handler(self, formatter):
        """파일 핸들러 추가 (로테이션 포함)"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, Config.LOGGING['log_file'])
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=Config.LOGGING['max_log_size'],
            backupCount=Config.LOGGING['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, Config.LOGGING['log_level']))
        
        self.logger.addHandler(file_handler)
    
    def _add_console_handler(self, formatter):
        """콘솔 핸들러 추가"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)  # 콘솔은 INFO 레벨 이상만
        
        self.logger.addHandler(console_handler)
    
    def _add_trading_handler(self, formatter):
        """거래 전용 로그 핸들러 추가"""
        log_dir = "logs"
        trading_log_file = os.path.join(log_dir, f"trading_{datetime.now().strftime('%Y%m%d')}.log")
        
        trading_handler = logging.FileHandler(
            filename=trading_log_file,
            encoding='utf-8'
        )
        
        # 거래 전용 포매터 (더 상세한 정보 포함)
        trading_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | TRADE | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trading_handler.setFormatter(trading_formatter)
        trading_handler.setLevel(logging.INFO)
        
        # 거래 관련 로그만 필터링
        trading_handler.addFilter(TradingLogFilter())
        
        self.logger.addHandler(trading_handler)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """정보 로그"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """에러 로그"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """치명적 에러 로그"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """메시지 포맷팅"""
        if kwargs:
            extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {extra_info}"
        return message
    
    # ========================================================================
    # 거래 전용 로그 메서드들
    # ========================================================================
    
    def log_login(self, success: bool, account_no: str = None):
        """로그인 로그"""
        if success:
            self.info("API_LOGIN_SUCCESS", account=account_no or Config.ACCOUNT_NO)
        else:
            self.error("API_LOGIN_FAILED", account=account_no or Config.ACCOUNT_NO)
    
    def log_market_data(self, symbol: str, price: float, volume: int = None):
        """시장 데이터 로그"""
        self.debug("MARKET_DATA_RECEIVED", 
                  symbol=symbol, price=price, volume=volume)
    
    def log_signal_generated(self, signal_type: str, symbol: str, conditions: dict):
        """시그널 생성 로그"""
        self.info("SIGNAL_GENERATED", 
                 type=signal_type, symbol=symbol, conditions=str(conditions))
    
    def log_order_request(self, order_type: str, symbol: str, quantity: int, 
                         price: float = None, order_id: str = None):
        """주문 요청 로그"""
        self.info("ORDER_REQUEST", 
                 type=order_type, symbol=symbol, quantity=quantity, 
                 price=price, order_id=order_id)
    
    def log_order_filled(self, symbol: str, quantity: int, price: float, 
                        order_id: str = None, commission: float = None):
        """주문 체결 로그"""
        self.info("ORDER_FILLED", 
                 symbol=symbol, quantity=quantity, price=price, 
                 order_id=order_id, commission=commission)
    
    def log_order_cancelled(self, order_id: str = None, reason: str = None):
        """주문 취소 로그"""
        self.warning("ORDER_CANCELLED", order_id=order_id, reason=reason)
    
    def log_position_opened(self, symbol: str, quantity: int, entry_price: float):
        """포지션 개시 로그"""
        self.info("POSITION_OPENED", 
                 symbol=symbol, quantity=quantity, entry_price=entry_price)
    
    def log_position_closed(self, symbol: str, quantity: int, exit_price: float, 
                           pnl: float = None, reason: str = None):
        """포지션 청산 로그"""
        self.info("POSITION_CLOSED", 
                 symbol=symbol, quantity=quantity, exit_price=exit_price, 
                 pnl=pnl, reason=reason)
    
    def log_stop_loss_triggered(self, symbol: str, current_price: float, 
                               stop_price: float, loss_percent: float):
        """손절매 실행 로그"""
        self.warning("STOP_LOSS_TRIGGERED", 
                    symbol=symbol, current_price=current_price, 
                    stop_price=stop_price, loss_percent=loss_percent)
    
    def log_ma_cross(self, symbol: str, ma_period: int, cross_type: str, 
                    current_price: float, ma_value: float):
        """이동평균선 교차 로그"""
        self.info("MA_CROSS_DETECTED", 
                 symbol=symbol, ma_period=ma_period, cross_type=cross_type,
                 current_price=current_price, ma_value=ma_value)
    
    def log_bollinger_squeeze(self, symbol: str, current_bandwidth: float, 
                             historical_low: float, squeeze_ratio: float):
        """볼린저밴드 스퀴즈 로그"""
        self.info("BOLLINGER_SQUEEZE_DETECTED", 
                 symbol=symbol, current_bandwidth=current_bandwidth,
                 historical_low=historical_low, squeeze_ratio=squeeze_ratio)
    
    def log_strategy_condition(self, condition_name: str, symbol: str, 
                              result: bool, details: dict = None):
        """전략 조건 체크 로그"""
        self.debug("STRATEGY_CONDITION_CHECK", 
                  condition=condition_name, symbol=symbol, 
                  result=result, details=str(details) if details else None)
    
    def log_risk_check(self, check_type: str, result: bool, details: dict = None):
        """리스크 체크 로그"""
        level = logging.WARNING if not result else logging.INFO
        self.logger.log(level, self._format_message("RISK_CHECK", 
                       type=check_type, passed=result, details=str(details) if details else None))
    
    def log_api_error(self, error_code: str = None, error_msg: str = None, 
                     function_name: str = None):
        """API 에러 로그"""
        self.error("API_ERROR", 
                  code=error_code, message=error_msg, function=function_name)
    
    def log_system_status(self, status: str, details: str = None):
        """시스템 상태 로그"""
        self.info("SYSTEM_STATUS", status=status, details=details)
    
    def log_performance_summary(self, total_trades: int, win_rate: float, 
                              total_pnl: float, max_drawdown: float):
        """성과 요약 로그"""
        self.info("PERFORMANCE_SUMMARY", 
                 total_trades=total_trades, win_rate=f"{win_rate:.2%}",
                 total_pnl=total_pnl, max_drawdown=max_drawdown)


class TradingLogFilter(logging.Filter):
    """거래 관련 로그만 필터링하는 필터"""
    
    TRADING_KEYWORDS = [
        'ORDER_', 'POSITION_', 'SIGNAL_', 'TRADE', 'FILLED', 
        'STOP_LOSS', 'MA_CROSS', 'BOLLINGER_SQUEEZE', 'PERFORMANCE_'
    ]
    
    def filter(self, record):
        """거래 관련 로그 메시지인지 확인"""
        message = record.getMessage()
        return any(keyword in message for keyword in self.TRADING_KEYWORDS)


class PerformanceLogger:
    """성과 측정 전용 로거"""
    
    def __init__(self, base_logger: TradingLogger):
        self.logger = base_logger
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0
        self.trades = []
    
    def log_trade_result(self, symbol: str, entry_price: float, exit_price: float, 
                        quantity: int, commission: float = 0):
        """거래 결과 로그 및 성과 집계"""
        pnl = (exit_price - entry_price) * quantity - commission
        is_win = pnl > 0
        
        trade_info = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'commission': commission,
            'timestamp': datetime.now()
        }
        
        self.trades.append(trade_info)
        self.trade_count += 1
        self.total_pnl += pnl
        
        if is_win:
            self.win_count += 1
        
        self.logger.info("TRADE_COMPLETED", 
                        symbol=symbol, pnl=f"{pnl:,.0f}", 
                        win=is_win, total_trades=self.trade_count)
    
    def get_performance_summary(self) -> dict:
        """성과 요약 반환"""
        if self.trade_count == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'max_drawdown': 0.0
            }
        
        win_rate = self.win_count / self.trade_count
        avg_pnl = self.total_pnl / self.trade_count
        
        # 최대 낙폭 계산
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in self.trades:
            cumulative_pnl += trade['pnl']
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_trades': self.trade_count,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_pnl': avg_pnl,
            'max_drawdown': max_drawdown
        }
    
    def log_daily_summary(self):
        """일일 성과 요약 로그"""
        summary = self.get_performance_summary()
        self.logger.log_performance_summary(
            summary['total_trades'],
            summary['win_rate'],
            summary['total_pnl'],
            summary['max_drawdown']
        )


# ============================================================================
# 전역 로거 인스턴스
# ============================================================================

# 메인 로거
main_logger = TradingLogger("KiwoomTrading")

# 모듈별 로거들
api_logger = TradingLogger("KiwoomAPI")
strategy_logger = TradingLogger("Strategy")
order_logger = TradingLogger("OrderManager")

# 성과 로거
performance_logger = PerformanceLogger(main_logger)

# ============================================================================
# 편의 함수들
# ============================================================================

def get_logger(module_name: str = "KiwoomTrading") -> TradingLogger:
    """모듈별 로거 반환"""
    loggers = {
        "KiwoomTrading": main_logger,
        "KiwoomAPI": api_logger,
        "Strategy": strategy_logger,
        "OrderManager": order_logger
    }
    return loggers.get(module_name, main_logger)

def log_system_start():
    """시스템 시작 로그"""
    main_logger.log_system_status("SYSTEM_STARTING", 
                                 f"Config: TestMode={Config.TEST_MODE['enabled']}")

def log_system_stop():
    """시스템 종료 로그"""
    # 최종 성과 요약 로그
    performance_logger.log_daily_summary()
    main_logger.log_system_status("SYSTEM_STOPPING")

def setup_exception_logging():
    """예외 처리 로그 설정"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            main_logger.info("SYSTEM_INTERRUPTED_BY_USER")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        main_logger.critical("UNCAUGHT_EXCEPTION", 
                           type=exc_type.__name__, 
                           message=str(exc_value))
    
    sys.excepthook = handle_exception

# ============================================================================
# 테스트 함수
# ============================================================================

def test_logger():
    """로거 테스트 함수"""
    print("🧪 로거 테스트 시작...")
    
    # 기본 로그 테스트
    main_logger.info("로거 테스트 시작")
    main_logger.debug("디버그 메시지 테스트")
    main_logger.warning("경고 메시지 테스트")
    main_logger.error("에러 메시지 테스트")
    
    # 거래 관련 로그 테스트
    main_logger.log_login(True)
    main_logger.log_signal_generated("BUY", "KOSPI200 C 330", {"ma_convergence": True})
    main_logger.log_order_request("BUY", "KOSPI200 C 330", 10, 0.25)
    main_logger.log_order_filled("KOSPI200 C 330", 10, 0.25, commission=1000)
    main_logger.log_position_opened("KOSPI200 C 330", 10, 0.25)
    main_logger.log_position_closed("KOSPI200 C 330", 10, 0.30, pnl=12500, reason="TAKE_PROFIT")
    
    # 성과 로거 테스트
    performance_logger.log_trade_result("KOSPI200 C 330", 0.25, 0.30, 10, 1000)
    performance_logger.log_daily_summary()
    
    print("✅ 로거 테스트 완료")
    print(f"로그 파일 위치: logs/{Config.LOGGING['log_file']}")

if __name__ == "__main__":
    test_logger()