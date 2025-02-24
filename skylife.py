import os
import re
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# .env 파일 로드
load_dotenv()

kakao_email = os.getenv("KAKAO_EMAIL")
kakao_password = os.getenv("KAKAO_PASSWORD")

def get_card_info(card_type):
    # 카드 종류에 따른 환경 변수 설정
    if card_type == "THEMOA":
        return {
            "card_number": os.getenv("THEMOA_CARD_NUMBER"),
            "expiry_year": os.getenv("THEMOA_CARD_EXPIRY_YEAR"),
            "expiry_month": os.getenv("THEMOA_CARD_EXPIRY_MONTH"),
            "birth_year": os.getenv("THEMOA_BIRTH_YEAR"),
            "birth_month": os.getenv("THEMOA_BIRTH_MONTH"),
            "birth_day": os.getenv("THEMOA_BIRTH_DAY"),
            "amt": os.getenv("THEMOA_AMT"),
            "password_prefix": os.getenv("THEMOA_PASSWORD_PREFIX")
        }
    elif card_type == "JJABMOA":
        return {
            "card_number": os.getenv("JJABMOA_CARD_NUMBER"),
            "expiry_year": os.getenv("JJABMOA_CARD_EXPIRY_YEAR"),
            "expiry_month": os.getenv("JJABMOA_CARD_EXPIRY_MONTH"),
            "birth_year": os.getenv("JJABMOA_BIRTH_YEAR"),
            "birth_month": os.getenv("JJABMOA_BIRTH_MONTH"),
            "birth_day": os.getenv("JJABMOA_BIRTH_DAY"),
            "amt": os.getenv("JJABMOA_AMT"),
            "password_prefix": os.getenv("JJABMOA_PASSWORD_PREFIX")
        }
    else:
        print("Invalid card type")
        return None

def run(context, card_type) -> bool:
    card_info = get_card_info(card_type)

    if card_info is None:
        return False  # 카드 정보가 잘못된 경우 종료

    page = context.new_page()
    page.goto("https://www.skylife.co.kr/member/login#enp_mbris")
    
    # 페이지가 완전히 로드될 때까지 대기
    page.wait_for_load_state('networkidle')
    
    # 카카오톡 로그인 링크 찾기 및 스크롤
    kakao_login_link = page.get_by_role("link", name="카카오톡 로그인")
    print("Scrolling to KakaoTalk login link...")
    kakao_login_link.scroll_into_view_if_needed()
    
    print("Clicking on KakaoTalk login...")
    with page.expect_popup() as page1_info:
        kakao_login_link.click()
    
    page1 = page1_info.value

    # 카카오 로그인이 되어 있는지 확인
    try:
        # 팝업이 자동으로 닫히는지 확인 (로그인 상태 유지된 경우)
        page1.wait_for_event('close', timeout=20000)
        print("Popup closed automatically. Kakao login is already completed.")
        
        if page.url == "https://www.skylife.co.kr/Main":
            # 페이지가 완전히 로드될 때까지 대기
            page.wait_for_load_state('networkidle')
            print("Redirected to Main page. Proceeding to payment...")
            return True  # 리다이렉션된 경우 로그인 완료로 처리
    
    except Exception:
        # 팝업이 닫히지 않았으므로 로그인 절차 필요
        print("Kakao login fields are visible. Completing login process...")
        
        # 로그인 필드가 나타나는 경우 로그인 절차 수행
        page1.wait_for_selector("input[placeholder='카카오메일 아이디, 이메일, 전화번호 ']", timeout=2000)
        page1.get_by_placeholder("카카오메일 아이디, 이메일, 전화번호 ").click()
        page1.get_by_placeholder("카카오메일 아이디, 이메일, 전화번호 ").type(kakao_email, delay=200)

        page1.get_by_placeholder("비밀번호").click()
        page1.get_by_placeholder("비밀번호").type(kakao_password, delay=200)
        page1.get_by_text("간편로그인 정보 저장").click()
        page1.get_by_role("button", name="로그인", exact=True).click()
        
        # 2단계 인증 비활성화
        button_locator = page1.get_by_text("이 브라우저에서 2단계 인증 사용 안 함")
        if button_locator.is_visible():
            button_locator.click()
        else:
            print("2단계 인증 버튼이 보이지 않습니다. 넘어갑니다.")
        page1.get_by_role("button", name="계속하기").click()

        print("Waiting for popup to close after login process...")
        page1.wait_for_event('close')

    print("Kakao login completed.")
    
    # 브라우저 상태 저장 (세션 및 쿠키)
    context.storage_state(path="storage_state.json")

    # 이후 페이지 이동 및 결제 작업 수행
    page.goto("https://www.skylife.co.kr/my/charge/pay/unpaid")
    page.get_by_role("link", name="신용카드로 결제하기").click()

    # 카드 정보 입력
    card_number = card_info['card_number']
    expiry_year = card_info['expiry_year']
    expiry_month = card_info['expiry_month']
    birth_year = card_info['birth_year']
    birth_month = card_info['birth_month']
    birth_day = card_info['birth_day']
    amt = card_info['amt']
    password_prefix = card_info['password_prefix']

    card_parts = []
    # 카드번호 입력 (형식 체크)
    if '-' in card_number:
        # xxxx-xxxx-xxxx-xxxx 형식
        card_parts = card_number.split("-")
        if len(card_parts) == 4 and all(len(part) == 4 and part.isdigit() for part in card_parts):
            card_parts = card_parts  # 카드 번호 각 부분을 담음
        else:
            print("카드 번호 형식이 잘못되었습니다.")
            return False
    else:
        # 1111222233334444 형식
        if len(card_number) == 16 and card_number.isdigit():
            card_parts = [card_number[i:i+4] for i in range(0, 16, 4)]  # 카드 번호 각 부분을 담음
        else:
            print("카드 번호 형식이 잘못되었습니다.")
            return False

    page.get_by_role("textbox", name="카드번호 첫 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 첫 번째 4자리").fill(card_parts[0])
    page.get_by_role("textbox", name="카드번호 두 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 두 번째 4자리").fill(card_parts[1])
    page.get_by_role("textbox", name="카드번호 세 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 세 번째 4자리").fill(card_parts[2])
    page.get_by_role("textbox", name="카드번호 네 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 네 번째 4자리").fill(card_parts[3])
    
    # 유효기간 입력
    # 카드 유효기간 년도 선택
    expiry_year_span = page.locator("th:has-text('카드유효기간') + td").locator("span").filter(has_text="년").locator("b").first
    expiry_year_span.click()
    page.locator("li").filter(has_text=expiry_year).click()

    # 카드 유효기간 월 선택
    expiry_month_span = page.locator("th:has-text('카드유효기간') + td").locator("span").filter(has_text="월").locator("b").first
    expiry_month_span.click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(expiry_month).click()

    # 생년월일 정보 입력
    # 생년월일 년도 선택
    birth_year_span = page.locator("th:has-text('생년월일') + td").locator("span").filter(has_text="년").locator("b").first
    birth_year_span.click()
    page.locator("li").filter(has_text=birth_year).click()

    # 생년월일 월 선택
    birth_month_span = page.locator("th:has-text('생년월일') + td").locator("span").filter(has_text="월").locator("b").first
    birth_month_span.click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(birth_month).click()

    # 생년월일 일 선택
    birth_day_span = page.locator("th:has-text('생년월일') + td").locator("span").filter(has_text="일").locator("b").first
    birth_day_span.click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(birth_day).click()

    # 결제 금액 입력
    page.locator('#monthlyCharge').fill(amt)
    
    # 카드 비밀번호 앞 두자리 입력
    page.get_by_role("textbox", name="비밀번호 앞 두자리 입력").click()
    page.get_by_role("textbox", name="비밀번호 앞 두자리 입력").fill(password_prefix)

    # 대화 상자 이벤트 리스너 등록
    page.on("dialog", handle_dialog)

    # 결제 버튼 클릭
    page.locator("a").filter(has_text=re.compile(r"^결제하기$")).click()
    
    # 다이얼로그 발생 대기 및 처리
    success = page.wait_for_event("dialog")

    context.close()
    return success

def handle_dialog(dialog):
    # 대화 상자 메시지 출력
    message = dialog.message  # 메서드가 아닌 속성으로 사용
    print("Dialog message:", message)
    
    # 성공과 실패 판별
    if "정상 결제되었습니다" in message:  # 성공 조건에 맞는 메시지
        print("Payment was successful!")
        dialog.dismiss()  # 다이얼로그 닫기
        return True
    else:
        print("Payment failed.")
        dialog.dismiss()  # 다이얼로그 닫기
        return False
    
def main():
    try:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir='user_data',
                locale="ko-KR",
                headless=False
            )

            if os.path.exists("storage_state.json"):
                print("Loading existing session state...")
                context.storage_state(path="storage_state.json")
            
            # card_types = ["THEMOA", "JJABMOA"]
            # card_types = ["JJABMOA"]
            card_types = ["THEMOA"]
            for card_type in card_types:
                success = run(context, card_type)
                if success:
                    print(f"Payment for {card_type} was successful. Proceeding to next card...")
                else:
                    print(f"Payment for {card_type} failed. Stopping process.")
                    break

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
