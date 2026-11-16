"""Smoke tests for the experimental reason / follow-up variants (dev/test split, artefact cleaning, phrasings)."""
from tools.followup_variants import follow_up_v1, follow_up_v2, load as load_fu
from tools.reason_variants import clean_note, split, v3


def test_split_is_odd_even_and_complete():
    ids = [f"ADI-{n:04d}" for n in range(1, 101)]
    dev, test = split(ids)
    assert len(dev) == len(test) == 50 and not set(dev) & set(test)
    assert dev[0] == "ADI-0001" and test[0] == "ADI-0002"


def test_clean_note_strips_generator_artefacts():
    raw = "Ecco la nota clinica domiciliare: 10/02/2026 ore 08:00. Visita. Nota: ho mantenuto i dati."
    out = clean_note(raw)
    assert out.startswith("10/02/2026") and "mantenuto" not in out


def test_reason_prefers_wound_action_over_generic_lead():
    text = ("21/02/2026 ore 14:00. Accesso domiciliare di controllo generale. Rilevati i seguenti parametri vitali: "
            "pressione arteriosa 130/80 mmHg. Eseguito cambio di medicazione e controllo della lesione.")
    assert v3(text) == "medicazione e controllo lesione"


def test_follow_up_timing_phrasings():
    base = "11/03/2026 ore 10:00. Visita. {}"
    for phrase, days in [("Nuovo controllo fra 3 giorni.", 3), ("Controllo programmato per i prossimi 2 giorni.", 2),
                         ("Si prevede un controllo domiciliare fra tre giorni.", 3),
                         ("Programmato nuovo controllo per il prossimo settimo giorno.", 7)]:
        assert follow_up_v2(base.format(phrase))["timing_days"] == days, phrase


def test_follow_up_date_arithmetic_and_scope():
    text = "11/03/2026 ore 10:00. Visita. Programmato controllo domiciliare in data 18/03/2026."
    assert follow_up_v1(text)["timing_days"] == 7
    # a wound mentioned outside the follow-up sentence must not change the type, and no plan means no follow-up
    assert follow_up_v1("10/02/2026 ore 08:00. Controllo della lesione da decubito presente.") is None
    out = follow_up_v1("10/02/2026 ore 08:00. Lesione medicata. Prossimo controllo programmato entro breve tempo.")
    assert out == {"type": "controllo", "timing_days": None}


def test_gold_loads():
    gold, text = load_fu()
    assert len(gold) == len(text) == 100


def test_generic_lesion_is_not_a_pressure_lesion():
    from tools.precision_rules import drop_generic_lesion
    assert drop_generic_lesion({"lesione_da_pressione", "dolore"}, "Controllo della lesione.") == {"dolore"}
    assert "lesione_da_pressione" in drop_generic_lesion({"lesione_da_pressione"}, "Lesione da decubito presente.")
