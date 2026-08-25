"""Write non-identifying coverage and completeness checks for the survey."""

import pandas as pd

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    PII_COLUMNS,
    TOPICS,
    load_survey,
)


def main() -> None:
    """Regenerate the aggregate survey audit table."""
    survey = load_survey()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    topic_counts = [
        survey[f"difficulty_{topic.casefold().replace(' ', '_')}"].notna().sum()
        for topic in TOPICS
    ]
    community_counts = survey["community"].value_counts()
    pd.DataFrame(
        [
            {
                "responses": len(survey),
                "direct_identifier_columns_removed": len(PII_COLUMNS),
                "communities": survey["community"].nunique(),
                "single_respondent_communities": (community_counts == 1).sum(),
                "respondents_in_single_respondent_communities": (
                    community_counts == 1
                ).sum(),
                "confidence_ratings_4_or_5": survey["confidence"].ge(4).sum(),
                "minimum_topic_responses": min(topic_counts),
                "maximum_topic_responses": max(topic_counts),
            }
        ]
    ).to_csv(OUTPUT_DIR / "survey_audit.csv", index=False)


if __name__ == "__main__":
    main()
