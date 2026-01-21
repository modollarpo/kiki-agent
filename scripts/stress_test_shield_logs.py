import time
import random
from core.creative_gallery import log_to_shield

def stress_test_shield_logs(n=100, delay=0.05):
    statuses = ['INFO', 'SHIELD-PASS', 'SHIELD-BLOCK']
    messages = [
        'Creative variant passed compliance.',
        'Blocked: Banned competitor "BrandX" detected.',
        'AI generated new TikTok ad.',
        'Blocked: Unsafe language detected.',
        'INFO: Starting creative generation.',
        'SHIELD-PASS: All checks passed.',
        'SHIELD-BLOCK: Copyrighted music detected.'
    ]
    for _ in range(n):
        status = random.choice(statuses)
        msg = random.choice(messages)
        log_to_shield(msg, status)
        time.sleep(delay)

if __name__ == "__main__":
    stress_test_shield_logs(200, 0.03)
