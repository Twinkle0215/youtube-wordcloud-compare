import re
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
from wordcloud import WordCloud

st.set_page_config(
    page_title="유튜브 동영상 2개 워드클라우드 비교 분석기", layout="wide"
)
st.title("📊 유튜브 동영상 2개 댓글 워드클라우드 비교 분석기")
st.caption("두 유튜브 링크를 입력하면 영상과 댓글 워드클라우드를 비교해 드립니다.")

# Streamlit Secrets에서 API 키 자동 불러오기
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error(
        "API 키가 설정되지 않았습니다. Streamlit App Settings -> Secrets 설정을 확인해주세요."
    )
    st.stop()

# 2개의 유튜브 링크 입력 창
col_input1, col_input2 = st.columns(2)

with col_input1:
    url1 = st.text_input(
        "첫 번째 동영상 링크",
        value="https://www.youtube.com/watch?v=j-JunRZuBkc",
    )
with col_input2:
    url2 = st.text_input(
        "두 번째 동영상 링크",
        value="https://www.youtube.com/watch?v=25JEQqgv5I4",
    )


def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else url


def get_comments_and_info(video_url, youtube_client):
    video_id = extract_video_id(video_url)

    # 영상 제목 가져오기
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
    if not url1 or not url2:
        st.warning("유튜브 동영상 링크 2개를 모두 입력해주세요.")
    else:
        try:
            youtube = build("youtube", "v3", developerKey=API_KEY)

            with st.spinner("댓글 데이터를 수집하고 워드클라우드를 생성 중입니다..."):
                title1, comments1 = get_comments_and_info(url1, youtube)
                title2, comments2 = get_comments_and_info(url2, youtube)

            if comments1 and comments2:
                col1, col2 = st.columns(2)

                # 첫 번째 영상
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

                # 두 번째 영상
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
                st.subheader("💡 분석 결과 요약")
                st.write(
                    f"- **영상 1 (`{title1}`):** 총 {len(comments1)}개 댓글 수집 완료"
                )
                st.write(
                    f"- **영상 2 (`{title2}`):** 총 {len(comments2)}개 댓글 수집 완료"
                )

            else:
                st.error(
                    "댓글을 가져올 수 없는 영상이 있습니다 (댓글 비활성화 여부 확인)."
                )

        except HttpError as e:
            st.error(f"API 오류가 발생했습니다: {e.reason}")
