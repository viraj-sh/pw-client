from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends
from typing import Annotated, Optional

from app.core.http import security, HTTPClientDep
from app.core.urls import API_BASE_URL
from app.core.constants import auth_headers
from app.schemas.quiz import (
    ResponseModel,
    SectionModel,
    SubjectModel,
    TopicModel,
    SubTopicModel,
    ChapterModel,
    QuestionModel,
    SolutionDescriptionModel,
    YourResultModel,
)


async def quiz_details(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    test_id: list[str],
):
    payload = {"testId": test_id}
    return await client.post(
        url=f"{API_BASE_URL}/v3/test-service/tests/user-test-student-mapping-list",
        json=payload,
        headers=auth_headers(token.credentials),
    )


async def quiz_result(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    test_mapping_id: str,
):
    return await client.get(
        url=f"{API_BASE_URL}/v3/test-service/tests/mapping/{test_mapping_id}/preview-test",
        headers=auth_headers(token.credentials),
    )


def _to_str(value):
    return str(value) if value is not None else None


def _build_image_url(base_url: Optional[str], key: Optional[str]) -> Optional[str]:
    if base_url and key:
        return f"{base_url}{key}"
    return None


def parse_quiz_result(raw: dict, root_id: str) -> ResponseModel:
    sections_raw = raw.get("data", {}).get("sections", [])
    sections = []

    for sec in sections_raw:
        sec_model = SectionModel(
            id=sec.get("sectionId", {}).get("_id") or "unknown",
            total_questions=_to_str(sec.get("totalQuestions")),
            un_attempted_questions=_to_str(sec.get("unAttemptedQuestions")),
            correct_questions=_to_str(sec.get("correctQuestions")),
            incorrect_questions=_to_str(sec.get("inCorrectQuestions")),
            questions_review=_to_str(sec.get("questionsUnderReview")),
        )

        for sub in sec.get("subjects", []):
            sub_model = SubjectModel(
                id=sub.get("subjectId", {}).get("_id") or "unknown",
                total_questions=_to_str(sub.get("totalQuestions")),
                un_attempted_questions=_to_str(sub.get("unAttemptedQuestions")),
                correct_questions=_to_str(sub.get("correctQuestions")),
                incorrect_questions=_to_str(sub.get("inCorrectQuestions")),
                questions_review=_to_str(sub.get("questionsUnderReview")),
                subject_name=sub.get("subjectId", {}).get("name"),
            )

            for ch in sub.get("chapters", []):
                ch_model = ChapterModel(
                    id=ch.get("chapterId", {}).get("_id") or "unknown",
                    total_questions=_to_str(ch.get("totalQuestions")),
                    un_attempted_questions=_to_str(ch.get("unAttemptedQuestions")),
                    correct_questions=_to_str(ch.get("correctQuestions")),
                    incorrect_questions=_to_str(ch.get("inCorrectQuestions")),
                    questions_review=_to_str(ch.get("questionsUnderReview")),
                    chapter_name=ch.get("chapterId", {}).get("name"),
                    chapter_id=ch.get("chapterId", {}).get("_id") or "unknown",
                )

                for top in ch.get("topics", []):
                    top_model = TopicModel(
                        id=top.get("topicId", {}).get("_id") or "unknown",
                        total_questions=_to_str(top.get("totalQuestions")),
                        un_attempted_questions=_to_str(top.get("unAttemptedQuestions")),
                        correct_questions=_to_str(top.get("correctQuestions")),
                        incorrect_questions=_to_str(top.get("inCorrectQuestions")),
                        questions_review=_to_str(top.get("questionsUnderReview")),
                        topic_name=top.get("topicId", {}).get("name"),
                    )

                    for st in top.get("subTopics", []):
                        st_model = SubTopicModel(
                            id=st.get("subTopicId", {}).get("_id") or "unknown",
                            total_questions=_to_str(st.get("totalQuestions")),
                            un_attempted_questions=_to_str(
                                st.get("unAttemptedQuestions")
                            ),
                            correct_questions=_to_str(st.get("correctQuestions")),
                            incorrect_questions=_to_str(st.get("inCorrectQuestions")),
                            questions_review=_to_str(st.get("questionsUnderReview")),
                            subtopic_name=st.get("subTopicId", {}).get("name"),
                        )
                        top_model.sub_topics.append(st_model)

                    ch_model.topics.append(top_model)

                sub_model.chapters.append(ch_model)

            sec_model.subjects.append(sub_model)

        sections.append(sec_model)

    questions_raw = raw.get("data", {}).get("questions", [])
    questions = []

    for q in questions_raw:
        q_data = q.get("question", {})
        your_result_data = q.get("yourResult", {})

        image_ids = q_data.get("imageIds", {})
        en_image = image_ids.get("en", {}) if isinstance(image_ids, dict) else {}

        sol_desc_list = []
        for sol_desc in q_data.get("solutionDescription", []):
            sol_img_ids = sol_desc.get("imageIds", {})
            sol_en = sol_img_ids.get("en", {}) if isinstance(sol_img_ids, dict) else {}
            sol_desc_model = SolutionDescriptionModel(
                sol_image_name=_to_str(sol_en.get("name")),
                sol_image_url=_build_image_url(
                    sol_en.get("baseUrl"), sol_en.get("key")
                ),
            )
            sol_desc_list.append(sol_desc_model)

        options = [
            opt.get("_id") for opt in q_data.get("options", []) if opt.get("_id")
        ]

        solutions = q_data.get("solutions", [])

        your_result_model = YourResultModel(
            is_under_review=_to_str(your_result_data.get("isUnderReview")),
            status=_to_str(your_result_data.get("status")),
            marked_solutions=your_result_data.get("markedSolutions", []),
            marked_solution_text=_to_str(your_result_data.get("markedSolutionText")),
            score=_to_str(your_result_data.get("score")),
            score_str=_to_str(your_result_data.get("scoreStr")),
            time_taken=_to_str(your_result_data.get("timeTaken")),
        )

        question_model = QuestionModel(
            id=q_data.get("_id") or "unknown",
            q_type=_to_str(q_data.get("type")),
            q_number=_to_str(q_data.get("questionNumber")),
            pos_marks=_to_str(q_data.get("positiveMarks")),
            neg_marks=_to_str(q_data.get("negativeMarks")),
            image_name=_to_str(en_image.get("name")),
            image_url=_build_image_url(en_image.get("baseUrl"), en_image.get("key")),
            options=options,
            diff_level=_to_str(q_data.get("difficultyLevel")),
            topic_name=_to_str(q_data.get("topicId", {}).get("name")),
            section_id=_to_str(q_data.get("sectionId")),
            subject_id=_to_str(q_data.get("subjectId")),
            chapter_id=_to_str(q_data.get("chapterId")),
            subtopic_id=_to_str(q_data.get("subTopicId")),
            solutions=solutions,
            solution_description=sol_desc_list,
            your_result=your_result_model,
        )
        questions.append(question_model)

    return ResponseModel(id=root_id, sections=sections, questions=questions)
