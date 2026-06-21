#!/usr/bin/env bash
# Deploy token refresher on QNAP for dual-IP token collection.
# Ruleaza pe QNAP (prin cron la fiecare 2 min) si colecteaza tokenuri
# de pe un IP diferit fata de Think (dubleaza rata de colectare).
# Path QNAP: /share/CACHEDEV1_DATA/Container/hermes-agent/data/tools/

scp "$0" admin@192.168.123.25:/share/CACHEDEV1_DATA/Container/hermes-agent/data/tools/qnap-token-refresh.py 2>/dev/null || {
    echo "QNAP nu e accesibil. Copiaza manual cand revine."
    exit 1
}

# Adauga cron pe QNAP
ssh admin@192.168.123.25 "crontab -l 2>/dev/null | grep -v qnap-token-refresh; echo '*/2 * * * * /usr/bin/python3 /share/CACHEDEV1_DATA/Container/hermes-agent/data/tools/qnap-token-refresh.py >> /share/CACHEDEV1_DATA/Container/hermes-agent/data/tools/qnap-token.log 2>&1' | crontab -"
echo "Cron adaugat pe QNAP"
