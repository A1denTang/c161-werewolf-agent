import pytest

from werewolf_agent.scoring import summarize, wilson


def row(match, role, outcome, *, status="completed", mode="practice"):
    return dict(match_id=match, role=role, side_result=outcome, seat="1", mode=mode,
                status=status, policy="carry", opponent_set="A")


def test_course_points_with_incomplete_games_kept_separate():
    games = [row("a", "wolf", "win"), row("b", "wolf", "loss"),
             row("c", "seer", "win"), row("d", "villager", "loss"),
             row("e", "", "", status="no_result"), row("f", "wolf", "win", mode="tournament")]
    summary = summarize(games)
    practice = summary[("practice", "carry")]
    assert practice["pending_or_void"] == 1
    assert practice["by_role"]["wolf"] == {"games": 2, "wins": 1, "points": 1}
    assert practice["by_role"]["seer"]["points"] == 1
    assert practice["by_role"]["villager"]["points"] == 0
    assert summary[("tournament", "carry")]["by_role"]["wolf"]["points"] == 2
    assert wilson(1, 2) == pytest.approx((0.09453, 0.90547), abs=0.0001)


def test_two_seats_from_one_table_cannot_be_two_games():
    with pytest.raises(ValueError, match="unique match ID"):
        summarize([row("same", "wolf", "win"), row("same", "villager", "loss")])
