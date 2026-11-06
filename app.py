import re
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
from wordcloud import WordCloud

# 페이지 레이아웃 및 제목 설정
st.set_page_config(
    page_title="유튜브 동영상 2개 워드클라우드 비교 분석기", layout="wide"
)
st.title("📊 유튜브 동영상 2개 댓글 워드클라우드 비교 분석기")

# 사이드바에서 API 키 입력 받기
with st.sidebar:
    st.header("🔑 설정")
    api_key = st.text_input("YouTube API Key 입력", type="password")
    st.caption("Colab Secrets의 YOUTUBE_API_KEY를 입력해주세요.")

# 2개의 유튜브 링크 입력 창 (나란히 배치)
col_input1, col_input2 = st.columns(2)

with col_input1:
    url1 = st.text_input(
        "첫 번째 동영상 링크",
        value="https://www.youtube.com/watch?v=j-JunRZuBkc",
    )
with col_input2:
    url2 = st.text_input("두 번째 동영상 링크", value="")


def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else url


def get_comments_and_info(video_url, youtube_client):
    video_id = extract_video_id(video_url)

    # 영상 정보(제목) 가져오기
    video_res = (
        youtube_client.videos().list(part="snippet", id=video_id).execute()
    )
    if not video_res.get("items"):
        return None, None

    title = video_res["items"][0]["snippet"]["title"]

    # 댓글 수집 (최대 300개)
    comments = []
    next_page_token = None

    for _ in range(3):
        res = (
            youtube_client.commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText",
            )
            .execute()
        )

        for item in res.get("items", []):
            comments.append(
                item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            )

        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    return title, comments


# 분석 시작 버튼
if st.button("🚀 두 영상 비교 분석 시작", use_container_width=True):
    if not api_key:
        st.error("좌측 사이드바에 YouTube API Key를 입력해주세요.")
    elif not url1 or not url2:
        st.warning("유튜브 동영상 링크 2개를 모두 입력해주세요.")
    else:
        try:
            youtube = build("youtube", "v3", developerKey=api_key)

            with st.spinner("댓글 데이터를 수집하고 시각화하는 중입니다..."):
                title1, comments1 = get_comments_and_info(url1, youtube)
                title2, comments2 = get_comments_and_info(url2, youtube)

            if comments1 and comments2:
                # 2열 레이아웃으로 결과 화면 구성
                col1, col2 = st.columns(2)

                # 첫 번째 영상 결과
                with col1:
                    st.subheader("🎬 동영상 1")
                    st.video(url1)
                    st.caption(f"**제목:** {title1}")

                    full_text1 = " ".join(comments1)
                    cleaned1 = re.sub(r"[^\w\s]", "", full_text1)
                    wc1 = WordCloud(
                        width=600,
                        height=400,
                        background_color="white",
                        max_words=100,
                        colormap="viridis",
                    ).generate(cleaned1)

                    fig1, ax1 = plt.subplots(figsize=(8, 5))
                    ax1.imshow(wc1, interpolation="bilinear")
                    ax1.axis("off")
                    st.pyplot(fig1)

                # 두 번째 영상 결과
                with col2:
                    st.subheader("🎬 동영상 2")
                    st.video(url2)
                    st.caption(f"**제목:** {title2}")

                    full_text2 = " ".join(comments2)
                    cleaned2 = re.sub(r"[^\w\s]", "", full_text2)
                    wc2 = WordCloud(
                        width=600,
                        height=400,
                        background_color="white",
                        max_words=100,
                        colormap="plasma",
                    ).generate(cleaned2)

                    fig2, ax2 = plt.subplots(figsize=(8, 5))
                    ax2.imshow(wc2, interpolation="bilinear")
                    ax2.axis("off")
                    st.pyplot(fig2)

                st.divider()
                st.subheader("💡 종합 비교 요약")
                st.write(
                    f"- **영상 1 수집 댓글 수:** {len(comments1)}개 | 주요 키워드 기반 반응 시각화 완료"
                )
                st.write(
                    f"- **영상 2 수집 댓글 수:** {len(comments2)}개 | 주요 키워드 기반 반응 시각화 완료"
                )

            else:
                st.error(
                    "댓글을 가져올 수 없는 영상이 포함되어 있습니다 (댓글 비활성화 여부 확인)."
                )

        except HttpError as e:
            st.error(f"API 오류가 발생했습니다: {e.reason}")
