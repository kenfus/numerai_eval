import json
from typing import Dict

import numerapi
import pandas as pd


def get_model_performance(model_name: str, last_n_rounds: int = 10000) -> pd.DataFrame:
    # provide api tokens
    keys = json.load(open("numerai_api_key.json"))
    napi = numerapi.NumerAPI(keys["pub_id"], keys["secret_key"])

    # upload predictions
    model_id = napi.get_models()[model_name]
    variables = {"modelId": model_id, "lastNRounds": last_n_rounds}
    query = """
        query($modelId: ID!, $lastNRounds: Int) {
        v2RoundModelPerformances(modelId: $modelId, lastNRounds: $lastNRounds) {
            atRisk
            corrMultiplier
            mmcMultiplier
            roundCloseStakingTime
            roundDataDatestamp
            roundId
            roundNumber
            roundOpenTime
            roundPayoutFactor
            roundResolveTime
            roundResolved
            roundScoreTime
            roundTarget
            submissionId
            tcMultiplier
            submissionScores {
            date
            day
            displayName
            payoutPending
            payoutSettled
            percentile
            value
            }
        }
        }
    """
    result = napi.raw_query(query, variables=variables)

    # Alot of filter and extraction
    filtered = result["data"]["v2RoundModelPerformances"]
    filtered = [x for x in filtered if x["roundResolved"] == True]
    results = []
    for round in filtered:
        round_dict = {}
        submission_scores = round.pop("submissionScores")
        round["model_name"] = model_name
        round_dict.update(round)
        for submission_scores in submission_scores:
            if submission_scores["day"] == 20:
                metric = submission_scores["displayName"]
                round_dict[metric] = submission_scores["value"]
                round_dict[metric + "_percentile"] = submission_scores["percentile"]
                round_dict.update(submission_scores)
        results.append(round_dict)
    return results


def query_answer_to_clean_df(answer: list[Dict]) -> pd.DataFrame:
    TO_DROP = [
        "roundOpenTime",
        "roundResolved",
        "submissionId",
        "roundScoreTime",
        "roundOpenTime",
        "roundId",
        "roundDataDatestamp",
        "roundCloseStakingTime",
        "day",
        "payoutPending",
        "payoutSettled",
        "atRisk",
        "roundTarget",
        "roundResolveTime",
        "percentile",
        "value",
        "displayName",
        "roundPayoutFactor",
        "corrMultiplier",
        "mmcMultiplier",
        "tcMultiplier",
        "corj60_percentile",
        "corj60",
    ]
    df = pd.DataFrame(answer).set_index("date", drop=True).sort_index()
    df = df.drop(columns=TO_DROP, errors="ignore")
    return df
