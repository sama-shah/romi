
DEFAULT_OUVLATION_FORGIVENESS_WINDOW_DAYS = 3

def compute_accuracy(labels: list, luteal_preds: set, warmup_period=0):
    total_correct = 0
    total_missing = 0

    for i in range(warmup_period, len(labels)):
        if labels[i] == 'missing':
            total_missing += 1
        elif labels[i] == 'luteal' or labels[i] == 'ovulation':
            if i in luteal_preds:
                total_correct += 1
        elif not(i in luteal_preds): # Not in preds means correct pred follicular
            total_correct += 1

    print(f"Out of {len(labels)} labels, {total_missing} are missing")
    return total_correct / (len(labels) - total_missing - warmup_period), total_correct, (len(labels) - total_missing - warmup_period)

def compute_ovulation_accuracy(labels: list, ovulation_preds: set, warmup_period=0, OUVLATION_FORGIVENESS_WINDOW_DAYS=DEFAULT_OUVLATION_FORGIVENESS_WINDOW_DAYS):
    total_correct = 0
    total_missing = 0

    for i in ovulation_preds:
        # Go over all values in the window and check if any of them are ovulation
        for j in range(i - OUVLATION_FORGIVENESS_WINDOW_DAYS, i + OUVLATION_FORGIVENESS_WINDOW_DAYS + 1):
            if labels[j] == 'ovulation':
                total_correct += 1
                break
        
    total_considered = labels[warmup_period:].count('ovulation')
    
    return total_correct / total_considered, total_correct, total_considered

def compute_fertility_accuracy(labels: list, fertility_preds: set, warmup_period=0):
    total_correct = 0
    total_missing = 0

    for i in fertility_preds:
        if labels[i] == 'ovulation' or labels[i] == 'fertile':
           total_correct += 1
        
    total_considered = labels[warmup_period:].count('ovulation') + labels[warmup_period:].count('fertile')

    return total_correct / total_considered, total_correct, total_considered



