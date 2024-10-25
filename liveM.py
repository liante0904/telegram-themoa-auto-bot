import time
import os
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright, card_type: str) -> None:
    # 카드 종류에 따른 환경 변수 설정
    if card_type == "THEMOA":
        card_number = os.getenv("THEMOA_CARD_NUMBER", "")
        expiry_month = os.getenv("THEMOA_CARD_EXPIRY_MONTH", "")
        expiry_year = os.getenv("THEMOA_CARD_EXPIRY_YEAR", "")
        name = os.getenv("THEMOA_NAME", "")
        birth_year = os.getenv("THEMOA_BIRTH_YEAR", "")
        birth_month = os.getenv("THEMOA_BIRTH_MONTH", "")
        birth_day = os.getenv("THEMOA_BIRTH_DAY", "")
        amount = os.getenv("THEMOA_AMT", "")
    elif card_type == "JJABMOA":
        card_number = os.getenv("JJABMOA_CARD_NUMBER", "")
        expiry_month = os.getenv("JJABMOA_CARD_EXPIRY_MONTH", "")
        expiry_year = os.getenv("JJABMOA_CARD_EXPIRY_YEAR", "")
        name = os.getenv("JJABMOA_NAME", "")
        birth_year = os.getenv("JJABMOA_BIRTH_YEAR", "")
        birth_month = os.getenv("JJABMOA_BIRTH_MONTH", "")
        birth_day = os.getenv("JJABMOA_BIRTH_DAY", "")
        amount = os.getenv("JJABMOA_AMT", "")
    else:
        print("Invalid card type")
        return

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(locale="ko-KR")
    page = context.new_page()

    # 페이지 이동
    page.goto("https://www.liivm.com/mypage/bill/bill/billPayment")
    time.sleep(1)

    # 로그인 유형
    page.get_by_role("link", name="아이디", exact=True).click()

    # 아이디 입력
    page.get_by_placeholder("KB Liiv M에 등록된 아이디를 입력해주세요").click()
    page.get_by_placeholder("KB Liiv M에 등록된 아이디를 입력해주세요").fill(os.getenv("LIVEM_ACCOUNT_EMAIL"))
    time.sleep(1)

    # 비밀번호 입력
    page.get_by_role("textbox", name="비밀번호를 입력해주세요").click()
    page.get_by_role("textbox", name="비밀번호를 입력해주세요").fill(os.getenv("LIVEM_ACCOUNT_PASSWORD"))
    time.sleep(1)

    # 로그인 버튼 클릭
    page.get_by_text("로그인 로그인 로그인").click()
    time.sleep(1)

    # 부분 납부 버튼 클릭
    page.get_by_role("link", name="부분 납부").click()
    time.sleep(1)

    # 부분 납부금액 입력
    page.get_by_label("부분 납부금액").click()
    page.get_by_label("부분 납부금액").fill(amount)
    time.sleep(1)

    # 다른 카드로 납부하기 버튼 클릭
    page.get_by_role("link", name="다른 카드로 납부하기").click()
    time.sleep(1)

    card_parts = []
    # 카드번호 입력 (형식 체크)
    if '-' in card_number:
        # xxxx-xxxx-xxxx-xxxx 형식
        card_parts = card_number.split("-")
        if len(card_parts) == 4 and all(len(part) == 4 and part.isdigit() for part in card_parts):
            card_parts = card_parts  # 카드 번호 각 부분을 담음
        else:
            print("카드 번호 형식이 잘못되었습니다.")
            return
    else:
        # 1111222233334444 형식
        if len(card_number) == 16 and card_number.isdigit():
            card_parts = [card_number[i:i+4] for i in range(0, 16, 4)]  # 카드 번호 각 부분을 담음
        else:
            print("카드 번호 형식이 잘못되었습니다.")
            return
    
    page.get_by_label("카드번호 ~ ~ ~").click()
    page.get_by_label("카드번호 ~ ~ ~").fill(card_parts[0])
    time.sleep(1)
    page.get_by_role("spinbutton", name="카드번호 둘째 자리 입력").fill(card_parts[1])
    time.sleep(1)
    page.get_by_role("spinbutton", name="카드번호 셋째 자리 입력").fill(card_parts[2])
    time.sleep(1)
    page.get_by_role("spinbutton", name="카드번호 마지막 자리 입력").fill(card_parts[3])
    time.sleep(1)

    # 유효기간 입력
    page.get_by_role("textbox", name="유효기간").click()
    page.get_by_role("textbox", name="유효기간").type(f"{expiry_month}{expiry_year[-2:]}", delay=200)
    time.sleep(1)

    # 카드 소유자 이름 입력
    page.get_by_placeholder("카드소유자 본인이름을 입력해주세요").click()
    page.get_by_placeholder("카드소유자 본인이름을 입력해주세요").fill(name)
    time.sleep(1)

    # 생년월일 입력
    page.get_by_placeholder("생년월일 8자리 (ex: 19850101)").click()
    page.get_by_placeholder("생년월일 8자리 (ex: 19850101)").fill(f"{birth_year}{birth_month}{birth_day}")
    time.sleep(1)

    # 카드 선택 및 입력 완료
    page.get_by_role("button", name="신한카드").click()
    time.sleep(1)
    page.get_by_role("button", name="입력완료").click()
    time.sleep(1)

    # 확인 버튼 클릭
    page.get_by_role("button", name="확인").click()

    # 카드 결제 버튼 클릭 (id로 접근)
    page.click("#btn_pym02Layer")

    # 성공 여부 확인
    try:
        # 로딩 완료될 때까지 기다림
        page.wait_for_selector('#message', state='visible', timeout=20000)

        # 메시지 읽어오기
        message_text = page.locator('#message').inner_text()

        # 성공 여부 확인
        if "등록된 카드로 청구 금액이 납부 처리되었습니다." in message_text:
            print(f"{card_type} 카드 결제 성공: {message_text}")
        else:
            print(f"{card_type} 카드 결제 실패: {message_text}")

    except Exception as e:
        print(f"{card_type} 카드 결제 중 오류 발생: {str(e)}")

    time.sleep(5000000)

    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright, card_type="THEMOA")  # 카드 종류에 따라 THEMOA 또는 JJABMOA 전달
    # run(playwright, card_type="JJABMOA")  # 카드 종류에 따라 THEMOA 또는 JJABMOA 전달
    