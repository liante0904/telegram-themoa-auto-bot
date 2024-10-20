import os
import re
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# .env 파일 로드
load_dotenv()


# 환경 변수에서 값 가져오기
kakao_email = os.getenv('KAKAO_EMAIL')
kakao_password = os.getenv('KAKAO_PASSWORD')
card_number = os.getenv('THEMOA_CARD_NUMBER')
expiry_year = os.getenv('THEMOA_CARD_EXPIRY_YEAR')
expiry_month = os.getenv('THEMOA_CARD_EXPIRY_MONTH')
birth_year = os.getenv('THEMOA_BIRTH_YEAR')
birth_month = os.getenv('THEMOA_BIRTH_MONTH')
birth_day = os.getenv('THEMOA_BIRTH_DAY')
amt = os.getenv('THEMOA_AMT')
password_prefix = os.getenv('THEMOA_PASSWORD_PREFIX')

def run(context) -> None:
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
        page1.wait_for_event('close', timeout=2000)
        print("Popup closed automatically. Kakao login is already completed.")
        
        if page.url == "https://www.skylife.co.kr/Main":
            print("Redirected to Main page. Proceeding to payment...")
            return  # 리다이렉션된 경우 로그인 완료로 처리
    
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
        page1.get_by_text("이 브라우저에서 2단계 인증 사용 안 함").click()
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
    page.get_by_role("textbox", name="카드번호 첫 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 첫 번째 4자리").fill(card_number[0:4])
    page.get_by_role("textbox", name="카드번호 두 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 두 번째 4자리").fill(card_number[4:8])
    page.get_by_role("textbox", name="카드번호 세 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 세 번째 4자리").fill(card_number[8:12])
    page.get_by_role("textbox", name="카드번호 네 번째 4자리").click()
    page.get_by_role("textbox", name="카드번호 네 번째 4자리").fill(card_number[12:16])

    # 유효기간 입력
    page.locator("span").filter(has_text="년").locator("b").click()
    page.locator("li").filter(has_text=expiry_year[-2:]).click()
    page.get_by_role("cell", name=f"{expiry_year[-2:]} ▾ 월 월 ▾").locator("b").nth(1).click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(expiry_month).click()

    # 생년월일 정보 입력
    page.locator("span").filter(has_text="년").locator("span").click()
    page.locator("li").filter(has_text=birth_year).click()
    page.locator("span").filter(has_text="월").locator("span").click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(birth_month).click()
    page.locator("span").filter(has_text="일").locator("b").click()
    page.locator("#payCreditCard").get_by_role("list").get_by_text(birth_day).click()

    # 결제 금액 입력
    page.locator('#monthlyCharge').fill(amt)
    
    # 카드 비밀번호 앞 두자리 입력
    page.get_by_role("textbox", name="비밀번호 앞 두자리 입력").click()
    page.get_by_role("textbox", name="비밀번호 앞 두자리 입력").fill(password_prefix)

    # 결제 버튼 클릭 및 대화 상자 처리
    page.locator("a").filter(has_text=re.compile(r"^결제하기$")).click()
    page.once("dialog", lambda dialog: handle_dialog(dialog))
    time.sleep(20)
    context.close()


def handle_dialog(dialog):
    # 대화 상자 메시지 출력
    message = dialog.message()
    print("Dialog message:", message)
    
    # 성공과 실패 판별
    if "성공" in message:  # 성공 조건에 맞는 메시지
        print("Payment was successful!")
    elif "실패" in message:  # 실패 조건에 맞는 메시지
        print("Payment failed.")
    
    # 대화 상자 닫기
    dialog.dismiss()


def main():
    try:
        with sync_playwright() as playwright:
            if os.path.exists("storage_state.json"):
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir='user_data',
                    headless=False
                )
                context.storage_state(path="storage_state.json")
            else:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir='user_data',
                    headless=False
                )

            if os.path.exists("storage_state.json"):
                print("Loading existing session state...")
                context.storage_state(path="storage_state.json")
                run(context)  # 세션 상태를 유지하면서 실행
            else:
                print("Navigating to login page...")
                page = context.new_page()
                page.goto("https://www.skylife.co.kr/member/login#enp_mbris")
                run(context)  # 새 세션으로 실행

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
