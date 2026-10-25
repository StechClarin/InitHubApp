#!/bin/bash
set -eo pipefail # Arrêt immédiat en cas d'erreur critique

echo "🚀 ==============================================="
echo "🚀 [INITHUB APP] DÉBUT DU DÉPLOIEMENT EN PRODUCTION"
echo "🚀 ==============================================="

# 1. Récupération du code le plus récent
echo ""
echo "📦 1/5. Récupération des dernières modifications Git..."
git fetch origin
git pull --rebase

# 2. Build et démarrage des conteneurs
echo ""
echo "🐳 2/5. Construction et démarrage des conteneurs..."
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# 3. Synchronisation optionnelle des seeders (uniquement avec ./deploy.sh --seed)
if [ "$1" == "--seed" ]; then
    echo ""
    echo "🌱 3/5. Synchronisation des modules applicatifs (Option --seed activée)..."
    docker compose -f docker-compose.prod.yml exec -T backend-test python manage.py seed_navigation || true
    docker compose -f docker-compose.prod.yml exec -T backend-test python manage.py seed_access || true
else
    echo ""
    echo "ℹ️  3/5. Seeders ignorés (Pour forcer le re-seeding des menus : ./deploy.sh --seed)"
fi

# 4. Nettoyage des anciennes images Docker (Protection disque VPS)
echo ""
echo "🧹 4/5. Nettoyage des images Docker orphelines..."
docker image prune -f

# 5. Healthcheck : Vérification que l'API répond bien 200 OK
echo ""
echo "🩺 5/5. Vérification de la santé du backend..."
sleep 3
if docker compose -f docker-compose.prod.yml exec -T backend-test python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/external/ping/', timeout=5)" > /dev/null 2>&1; then
    echo "✅ Backend InitHub App en ligne et opérationnel !"
else
    echo "⚠️ Attention : Le backend ne répond pas au ping de santé. Vérifiez les logs :"
    docker compose -f docker-compose.prod.yml logs --tail=50 backend-test
    exit 1
fi

echo ""
echo "🎉 ==============================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "🎉 ==============================================="
docker compose -f docker-compose.prod.yml ps
