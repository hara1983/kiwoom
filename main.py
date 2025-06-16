# main.py 파일에 이 코드를 붙여넣으세요.

import time
# 'kiwoom_api.py' 파일에서 KiwoomAPI 클래스를 가져옵니다.
from kiwoom_api import KiwoomAPI 

if __name__ == "__main__":
    api = KiwoomAPI()
    
    try:
        # 키움 API 연결 (로그인 창 표시)
        if api.connect():
            print("로그인 성공! 테스트를 시작합니다.")
            
            # 여기에 원하는 기능 테스트 코드를 넣으시면 됩니다.
            print("\n[테스트] 위클리 옵션 조회...")
            options = api.get_weekly_option_codes()
            if options:
                print(f"조회된 옵션 개수: {len(options)}")
                print(f"첫 번째 옵션 정보: {options[0]}")
            else:
                print("옵션 조회에 실패했거나, 조회된 옵션이 없습니다.")
            
            print("\n모든 테스트 완료. 5초 후 프로그램을 종료합니다.")
            time.sleep(5)

    except Exception as e:
        print(f"메인 실행 중 오류 발생: {e}")
    
    finally:
        # 프로그램 종료 시 API 연결 해제
        api.disconnect()
        print("프로그램을 종료합니다.")