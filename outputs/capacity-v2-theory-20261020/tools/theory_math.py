"""Theory arithmetic helpers, not a model architecture or deployment adapter."""
import math

def positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(name + ' must be finite and positive')
    return value

def count(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(name + ' must be a positive integer')
    return value

def planned_concurrency(requests, growth_percent):
    count(requests, 'requests')
    if isinstance(growth_percent, bool) or not isinstance(growth_percent, (int, float)) or not math.isfinite(growth_percent) or growth_percent < 0:
        raise ValueError('growth_percent must be finite and nonnegative')
    return math.ceil(requests * (1 + growth_percent / 100))

def linear_work_top(tokens, active_parameters):
    """Only the 2*active matrix arithmetic approximation; not total model work."""
    return positive(tokens, 'tokens') * positive(active_parameters, 'active_parameters') * 2 / 1e12

def mean_fcfs_order(requests, instances):
    """Balanced equal-service sequential FCFS; includes exact uneven assignment."""
    count(requests, 'requests'); count(instances, 'instances')
    q, r = divmod(requests, instances)
    return ((instances-r)*q*(q+1)/2 + r*(q+1)*(q+2)/2) / requests

def effective_tops(physical_cards, peak_tops_per_card, efficiency):
    count(physical_cards, 'physical_cards')
    positive(peak_tops_per_card, 'peak_tops_per_card'); positive(efficiency, 'efficiency')
    if efficiency > 1: raise ValueError('efficiency must be <= 1')
    return physical_cards * peak_tops_per_card * efficiency

def burst_mean_ttft_ms(requests, instances, single_request_work_top, instance_effective_tops, fixed_ms):
    positive(single_request_work_top, 'single_request_work_top'); positive(instance_effective_tops, 'instance_effective_tops')
    if not isinstance(fixed_ms, (int, float)) or isinstance(fixed_ms, bool) or not math.isfinite(fixed_ms) or fixed_ms < 0:
        raise ValueError('fixed_ms must be finite and nonnegative')
    return mean_fcfs_order(requests, instances) * single_request_work_top / instance_effective_tops * 1000 + fixed_ms

def card_totals(work_groups, cards_per_group, spare_groups):
    count(work_groups, 'work_groups'); count(cards_per_group, 'cards_per_group')
    if type(spare_groups) is not int or spare_groups < 0: raise ValueError('spare_groups must be a nonnegative integer')
    work=work_groups*cards_per_group; spare=spare_groups*cards_per_group
    return {'workCards':work, 'spareCards':spare, 'totalCards':work+spare}
