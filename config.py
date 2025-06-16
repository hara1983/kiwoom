# config.py - 키움증권 API 시스템 트레이딩 설정 파일
# ============================================================================

class Config:
    """키움증권 API 시스템 트레이딩 설정"""
    
    # ========================================================================
    # 계좌 정보
    # ========================================================================
    ACCOUNT_NO = "7028-1544"  # 모의투자 계좌번호
    
    # ========================================================================
    # 옵션 선택 기준
    # ========================================================================
    # 옵션 가격 필터링
    MIN_OPTION_PRICE = 0.1    # 최소 옵션 가격 (이하 제외)
    MAX_OPTION_PRICE = 0.3    # 선호 최대 옵션 가격
    PREFERRED_PRICE_RANGE = (0.1, 0.3)  # 선호 가격 범위
    
    # 대안 옵션 선택 (가격 범위 내 옵션이 없을 경우)
    ALTERNATIVE_OTM_LEVELS = [2, 3]  # 2외가, 3외가 옵션 우선순위
    
    # 옵션 타입 선택
    OPTION_TYPES = ['CALL', 'PUT']  # 콜/풋 옵션 모두 고려
    
    # ========================================================================
    # 전략 파라미터 - MA_Convergence (이동평균선 밀집도)
    # ========================================================================
    MA_CONVERGENCE = {
        'period1': 5,      # 단기 이동평균선 기간
        'period2': 20,     # 중기 이동평균선 기간
        'period3': 60,     # 장기 이동평균선 기간
        'price_type': 'close',  # 가격 종류 (close, open, high, low)
        'ma_type': 'SMA',  # 이동평균 방법 (SMA: 단순이동평균)
        'convergence_threshold': 0.5  # 밀집도 임계값 (조정 필요)
    }
    
    # ========================================================================
    # 전략 파라미터 - AbsBandwidthHistory (절대 밴드폭 역사적 최저)
    # ========================================================================
    BOLLINGER_BANDS = {
        'period': 20,      # 볼린저밴드 계산 기간
        'mult': 2,         # 표준편차 승수 (2시그마)
        'price_type': 'close',  # 가격 종류
        'ma_type': 'SMA',  # 이동평균 방법
        'lookback_period': 100,  # 과거 밴드폭 최저치 비교 기간
        'squeeze_threshold': 0.95  # 스퀴즈 판단 임계값 (현재 밴드폭/최저 밴드폭)
    }
    
    # ========================================================================
    # 차트 설정
    # ========================================================================
    CHART_TIMEFRAME = 3  # 3분봉
    CHART_PERIOD_COUNT = 200  # 조회할 봉 개수
    
    # ========================================================================
    # 매매 전략 설정
    # ========================================================================
    TRADING_STRATEGY = {
        # 매수 조건
        'buy_conditions': {
            'ma_convergence_required': True,    # 이동평균선 밀집 조건
            'bollinger_squeeze_required': True,  # 볼린저밴드 스퀴즈 조건
            'both_conditions_required': True     # 두 조건 모두 만족 필요
        },
        
        # 매도 조건
        'sell_conditions': {
            'ma10_cross_below': True,  # 10봉 이동평균 하향 돌파 시 매도
            'stop_loss_percent': 10,   # 손절매 퍼센트 (10%)
            'ma10_period': 10          # 매도 기준 이동평균 기간
        },
        
        # 주문 설정
        'order_settings': {
            'order_type': 'market',     # 시장가 주문 (market) 또는 지정가 (limit)
            'spread_tolerance': 0.05,   # 스프레드 허용 범위
            'price_adjustment_step': 0.01,  # 호가 조정 단위
            'max_order_attempts': 5,    # 최대 주문 시도 횟수
            'order_retry_delay': 1      # 주문 재시도 대기 시간 (초)
        }
    }
    
    # ========================================================================
    # 리스크 관리
    # ========================================================================
    RISK_MANAGEMENT = {
        'max_position_size': 1000000,    # 최대 포지션 크기 (원)
        'max_daily_loss': 500000,        # 일일 최대 손실 (원)
        'max_concurrent_positions': 3,   # 최대 동시 포지션 수
        'position_size_percent': 0.1     # 계좌 대비 포지션 크기 비율
    }
    
    # ========================================================================
    # API 설정
    # ========================================================================
    API_SETTINGS = {
        'request_delay': 0.2,        # API 요청 간격 (초)
        'login_timeout': 30,         # 로그인 타임아웃 (초)
        'data_timeout': 10,          # 데이터 수신 타임아웃 (초)
        'retry_count': 3             # 재시도 횟수
    }
    
    # ========================================================================
    # 로그 설정
    # ========================================================================
    LOGGING = {
        'log_level': 'INFO',         # 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        'log_file': 'kiwoom_trading.log',  # 로그 파일명
        'max_log_size': 10 * 1024 * 1024,  # 최대 로그 파일 크기 (10MB)
        'backup_count': 5,           # 로그 파일 백업 개수
        'console_output': True       # 콘솔 출력 여부
    }
    
    # ========================================================================
    # 테스트 모드 설정
    # ========================================================================
    TEST_MODE = {
        'enabled': True,             # 테스트 모드 활성화
        'paper_trading': True,       # 모의투자 사용
        'simulation_mode': False,    # 시뮬레이션 모드 (실제 주문 없음)
        'test_symbols': ['KOSPI200 C 330 2024-12-26'],  # 테스트용 종목
    }
    
    # ========================================================================
    # 주요 코스피200 지수 관련 설정
    # ========================================================================
    KOSPI200_SETTINGS = {
        'base_symbol': 'KOSPI200',
        'option_multiplier': 250000,  # 옵션 승수
        'tick_size': 0.01,           # 최소 호가 단위
        'trading_hours': {
            'start': '09:00',
            'end': '15:20'
        }
    }

# ============================================================================
# 설정 검증 함수
# ============================================================================
def validate_config():
    """설정값 유효성 검증"""
    errors = []
    
    # 계좌번호 검증
    if not Config.ACCOUNT_NO or len(Config.ACCOUNT_NO) < 8:
        errors.append("유효하지 않은 계좌번호입니다.")
    
    # 옵션 가격 범위 검증
    if Config.MIN_OPTION_PRICE >= Config.MAX_OPTION_PRICE:
        errors.append("최소 옵션 가격이 최대 옵션 가격보다 크거나 같습니다.")
    
    # 전략 파라미터 검증
    if Config.MA_CONVERGENCE['period1'] >= Config.MA_CONVERGENCE['period2']:
        errors.append("단기 이동평균 기간이 중기 이동평균 기간보다 크거나 같습니다.")
    
    if Config.MA_CONVERGENCE['period2'] >= Config.MA_CONVERGENCE['period3']:
        errors.append("중기 이동평균 기간이 장기 이동평균 기간보다 크거나 같습니다.")
    
    # 손절매 비율 검증
    stop_loss = Config.TRADING_STRATEGY['sell_conditions']['stop_loss_percent']
    if stop_loss <= 0 or stop_loss > 50:
        errors.append("손절매 비율이 유효하지 않습니다. (0 < 손절매 <= 50)")
    
    if errors:
        raise ValueError("설정 오류:\n" + "\n".join(errors))
    
    return True

# ============================================================================
# 설정 로드 함수
# ============================================================================
def get_config():
    """설정 객체 반환 (검증 포함)"""
    validate_config()
    return Config

if __name__ == "__main__":
    # 설정 검증 테스트
    try:
        config = get_config()
        print("✅ 설정 검증 완료")
        print(f"계좌번호: {config.ACCOUNT_NO}")
        print(f"옵션 가격 범위: {config.MIN_OPTION_PRICE} ~ {config.MAX_OPTION_PRICE}")
        print(f"차트 기간: {config.CHART_TIMEFRAME}분봉")
        print(f"손절매 비율: {config.TRADING_STRATEGY['sell_conditions']['stop_loss_percent']}%")
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")