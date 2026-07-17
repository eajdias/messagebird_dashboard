from datetime import datetime


class MetricsCalculator:
    # Thresholds configuráveis (sobrescritos por business_bsc.json via config_loader)
    nps_promoter_min = 9
    nps_passive_min = 7
    sla_threshold_minutes = 60

    @staticmethod
    def calculate_nps(scores: list[float]) -> float | None:
        """Calcula o NPS (Net Promoter Score)."""
        valid_scores = [v for v in scores if isinstance(v, (int, float))]
        if not valid_scores:
            return None
        promoters = sum(1 for v in valid_scores if v >= MetricsCalculator.nps_promoter_min)
        detractors = sum(1 for v in valid_scores if v < MetricsCalculator.nps_passive_min)
        total = len(valid_scores)
        return round((promoters - detractors) / total * 100, 2)

    @staticmethod
    def calculate_sla_rate(arts: list[float], threshold: int | None = None) -> float | None:
        """Calcula a taxa de conformidade SLA (%) baseada no ART."""
        if threshold is None:
            threshold = MetricsCalculator.sla_threshold_minutes
        valid_arts = [a for a in arts if isinstance(a, (int, float))]
        if not valid_arts:
            return None
        hits = sum(1 for a in valid_arts if a <= threshold)
        return round((hits / len(valid_arts)) * 100, 2)

    @staticmethod
    def calculate_rating_average(values: list[float]) -> float | None:
        """Alias para calculate_average, focado em ratings."""
        return MetricsCalculator.calculate_average(values)

    @staticmethod
    def calculate_frt(start_dt: datetime | None, first_resp_dt: datetime | None) -> float | None:
        """Calculates FRT (First Response Time) in minutes. No longer restricted to same-day."""
        if not start_dt or not first_resp_dt or start_dt >= first_resp_dt:
            return None

        delta = (first_resp_dt - start_dt).total_seconds() / 60
        return round(delta, 2)

    @staticmethod
    def calculate_average(values: list[float]) -> float | None:
        """Calcula a média de uma lista de valores."""
        valid_values = [v for v in values if isinstance(v, (int, float))]
        if not valid_values:
            return None
        return round(sum(valid_values) / len(valid_values), 2)

    @staticmethod
    def calculate_nps_distribution(scores: list[float]) -> dict:
        """Calcula a distribuição quantitativa do NPS (Promotores, Neutros, Detratores)."""
        valid_scores = [v for v in scores if isinstance(v, (int, float))]
        dist = {"promoters": 0, "passives": 0, "detractors": 0}
        for v in valid_scores:
            if v >= MetricsCalculator.nps_promoter_min:
                dist["promoters"] += 1
            elif v >= MetricsCalculator.nps_passive_min:
                dist["passives"] += 1
            else:
                dist["detractors"] += 1
        return dist

    @staticmethod
    def calculate_rating_distribution(values: list[float]) -> dict:
        """Calcula a distribuição quantitativa das notas (1 a 5)."""
        valid_values = [v for v in values if isinstance(v, (int, float))]
        dist = {str(i): 0 for i in range(1, 6)}
        for v in valid_values:
            key = str(int(v))
            if key in dist:
                dist[key] += 1
        return dist
