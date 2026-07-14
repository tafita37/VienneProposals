import json
import numpy as np
import os
import requests
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from authentification.decoratos import admin_required, user_required
from chatbot.metier.AdminChatMessage import AdminChatMessage
from chatbot.metier.CommercialChatMessage import CommercialChatMessage
from ..ai_server import LocalEmbeddingServer
from chatbot.metier.HelpDocument import HelpDocument

@require_POST
@admin_required
def chatbot_response_admin(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée. Utilisez POST."}, status=405)

    try:
        data = json.loads(request.body)
        admin_message = data.get("message", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"reply": "Format JSON invalide."})

    if not admin_message:
        return JsonResponse({"reply": "Dis-moi ce que tu veux faire."})

    # 1. GESTION DE L'HISTORIQUE DE SESSION GLISSANT
    if 'chat_history_admin' not in request.session:
        request.session['chat_history_admin'] = []
    history = request.session['chat_history_admin']

    # 2. RAG LOCAL : RECHERCHE ET SEUILS SÉMANTIQUES
    all_docs = list(HelpDocument.objects.all())
    if not all_docs:
        return JsonResponse({"reply": "Aucune documentation n'est disponible pour le moment."})

    try:
        model_embed = LocalEmbeddingServer.get_model()
        doc_texts = []
        for doc in all_docs:
            # Structure de base immuable
            text_format = (
                f"FONCTIONNALITÉ : {doc.title}\n"
                f"PUBLIC CIBLE : {doc.level}\n"
                f"TYPE DE PROBLÈME : {doc.type}\n"
            )
            
            # Ajout conditionnel de l'étape si elle existe
            if doc.step:
                text_format += f"CONTEXTE / ÉTAPE : {doc.step}\n"
                
            text_format += f"EXPLICATION : {doc.content}"
            
            doc_texts.append(text_format)
        
        # Encodage vectoriel en RAM
        doc_embeddings = model_embed.encode(doc_texts, convert_to_numpy=True)
        query_embedding = model_embed.encode(admin_message, convert_to_numpy=True)
        
        # Calcul de similarité cosinus (proximité du sens)
        scores = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Sélection des deux paragraphes les plus proches
        top_indices = np.argsort(scores)[-15:][::-1]
        
        # Filtre de sécurité strict fixé à 0.45
        relevant_paragraphs = [doc_texts[idx] for idx in top_indices]
        
    except Exception as e:
        return JsonResponse({"reply": "Erreur lors de l'analyse locale du contexte."})

    domaine=os.environ.get("DOMAIN_LINK")
    # 3. STRATÉGIE DE CADRAGE DU PROMPT
    if relevant_paragraphs:
        context = "\n".join(relevant_paragraphs)
        system_instruction = (
            f"Tu es l'assistant du CRM de Vienne Agencement. Aide l'administrateur nommé {request.user.first_name} en te basant sur les extraits fournis. Généralement le plus utile sera les informations avec pour public cible admin mais il peut arriver que tu aies besoin d'information dans les parties public cible commercial\n"
            "CONSIGNE DE RAISONNEMENT : Si l'action demandée n'est pas écrite mot pour mot mais qu'elle se déduit "
            "logiquement et avec certitude des instructions ou de l'historique récent, fais la déduction pour guider l'administrateur.\n"
            "Si les extraits ne permettent pas de déduire la réponse avec certitude, dis-le clairement sans inventer."
            "Pour toute explication nécéssitant d'indiquer un cheminent dans le CRM, utilise le nom de domaine suivant : " + domaine + " suivi du lien indiqué dans la documentation.\n"
        )
    else:
        context = "AUCUN DOCUMENT RELEVANT TROUVÉ DANS LA BASE DE DONNÉES."
        system_instruction = (
            f"Tu es l'assistant du CRM de Vienne Agencement. L'administrateur nommé {request.user.first_name} pose une question sur une fonctionnalité "
            "qui n'est pas documentée ou qui n'existe pas dans le système. Réponds poliment et de manière très concise "
            "que cette action n'est pas prise en charge ou documentée dans le CRM actuel. Ne propose pas de solution générique."
        )

    # 4. ENCAPSULATION DES MESSAGES AVEC MEMOIRE
    messages = [
        {"role": "system", "content": f"{system_instruction}\n\nCONTEXTE DISPONIBLE :\n{context}"}
    ]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": admin_message})

    # 5. REQUÊTE VERS L'API GROQ
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    URL = "https://api.groq.com/openai/v1/chat/completions"
    HEADERS = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.1,  # Précision froide, pas d'hallucination créative
        "max_tokens": 150    # Réponses courtes et directes pour économiser le quota
    }

    try:
        response = requests.post(URL, json=payload, headers=HEADERS, timeout=4)
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content'].strip()
            
            # Mise à jour et nettoyage de l'historique (max 6 messages / 3 tours)
            history.append({"role": "user", "content": admin_message})
            history.append({"role": "assistant", "content": reply})
            AdminChatMessage.objects.create(admin=request.user, role='user', content=admin_message)
            AdminChatMessage.objects.create(admin=request.user, role='assistant', content=reply)
            if len(history) > 6:
                history = history[-6:]
            request.session['chat_history_admin'] = history
        else:
            reply = "Le service d'analyse est temporairement saturé."
            
    except requests.exceptions.Timeout:
        reply = "L'analyseur externe a mis trop de temps à répondre."
    except Exception:
        reply = "Erreur de connexion avec le module de raisonnement."

    return JsonResponse({"reply": reply})

@require_POST
@user_required
def chatbot_response_commercial(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée. Utilisez POST."}, status=405)

    try:
        data = json.loads(request.body)
        commercial_message = data.get("message", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"reply": "Format JSON invalide."})

    if not commercial_message:
        return JsonResponse({"reply": "Dis-moi ce que tu veux faire."})

    # 1. GESTION DE L'HISTORIQUE DE SESSION GLISSANT
    if 'chat_history_commercial' not in request.session:
        request.session['chat_history_commercial'] = []
    history = request.session['chat_history_commercial']

    # 2. RAG LOCAL : RECHERCHE ET SEUILS SÉMANTIQUES
    all_docs = list(HelpDocument.objects.filter(level='commercial'))
    if not all_docs:
        return JsonResponse({"reply": "Aucune documentation n'est disponible pour le moment."})

    try:
        model_embed = LocalEmbeddingServer.get_model()
        doc_texts = []
        for doc in all_docs:
            # Structure de base immuable
            text_format = (
                f"FONCTIONNALITÉ : {doc.title}\n"
                f"PUBLIC CIBLE : {doc.level}\n"
                f"TYPE DE PROBLÈME : {doc.type}\n"
            )
            
            # Ajout conditionnel de l'étape si elle existe
            if doc.step:
                text_format += f"CONTEXTE / ÉTAPE : {doc.step}\n"
                
            text_format += f"EXPLICATION : {doc.content}"
            
            doc_texts.append(text_format)
        
        # Encodage vectoriel en RAM
        doc_embeddings = model_embed.encode(doc_texts, convert_to_numpy=True)
        query_embedding = model_embed.encode(commercial_message, convert_to_numpy=True)
        
        # Calcul de similarité cosinus (proximité du sens)
        scores = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Sélection des deux paragraphes les plus proches
        top_indices = np.argsort(scores)[-15:][::-1]
        
        # Filtre de sécurité strict fixé à 0.45
        relevant_paragraphs = [doc_texts[idx] for idx in top_indices]
        
    except Exception as e:
        return JsonResponse({"reply": "Erreur lors de l'analyse locale du contexte."})

    domaine=os.environ.get("DOMAIN_LINK")
    # 3. STRATÉGIE DE CADRAGE DU PROMPT
    if relevant_paragraphs:
        context = "\n".join(relevant_paragraphs)
        system_instruction = (
            f"Tu es l'assistant du CRM de Vienne Agencement. Tu es chargé d'aider le commercial nommé {request.user.first_name} en te basant sur les extraits fournis.\n"
            "CONSIGNE DE RAISONNEMENT : Si l'action demandée n'est pas écrite mot pour mot mais qu'elle se déduit "
            "logiquement et avec certitude des instructions ou de l'historique récent, fais la déduction pour guider le commercial.\n"
            "Si les extraits ne permettent pas de déduire la réponse avec certitude, dis-le clairement sans inventer."
            "Pour toute explication nécéssitant d'indiquer un cheminent dans le CRM, utilise le nom de domaine suivant : " + domaine + " suivi du lien indiqué dans la documentation.\n"
        )
    else:
        context = "AUCUN DOCUMENT RELEVANT TROUVÉ DANS LA BASE DE DONNÉES."
        system_instruction = (
            f"Tu es l'assistant du CRM de Vienne Agencement. Le commercial nommé {request.user.first_name} pose une question sur une fonctionnalité "
            "qui n'est pas documentée ou qui n'existe pas dans le système. Réponds poliment et de manière très concise "
            "que cette action n'est pas prise en charge ou documentée dans le CRM actuel. Ne propose pas de solution générique."
        )

    # 4. ENCAPSULATION DES MESSAGES AVEC MEMOIRE
    messages = [
        {"role": "system", "content": f"{system_instruction}\n\nCONTEXTE DISPONIBLE :\n{context}"}
    ]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": commercial_message})

    # 5. REQUÊTE VERS L'API GROQ
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    URL = "https://api.groq.com/openai/v1/chat/completions"
    HEADERS = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.1,  # Précision froide, pas d'hallucination créative
        "max_tokens": 150    # Réponses courtes et directes pour économiser le quota
    }

    try:
        response = requests.post(URL, json=payload, headers=HEADERS, timeout=4)
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content'].strip()
            
            # Mise à jour et nettoyage de l'historique (max 6 messages / 3 tours)
            history.append({"role": "user", "content": commercial_message})
            history.append({"role": "assistant", "content": reply})
            CommercialChatMessage.objects.create(commercial=request.user, role='user', content=commercial_message)
            CommercialChatMessage.objects.create(commercial=request.user, role='assistant', content=reply)
            if len(history) > 6:
                history = history[-6:]
            request.session['chat_history_commercial'] = history
        else:
            reply = "Le service d'analyse est temporairement saturé."
            
    except requests.exceptions.Timeout:
        reply = "L'analyseur externe a mis trop de temps à répondre."
    except Exception:
        reply = "Erreur de connexion avec le module de raisonnement."

    return JsonResponse({"reply": reply})