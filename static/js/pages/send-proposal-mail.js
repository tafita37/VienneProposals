// Scripts spécifiques: envoi d'une proposition commerciale par mail

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('mail-form');
    if (!form) {
        return;
    }

    const toInput = document.getElementById('mail-to');
    const ccInput = document.getElementById('mail-cc');
    const subjectInput = document.getElementById('mail-subject');
    const bodyInput = document.getElementById('mail-body');
    const counter = document.getElementById('mail-counter');
    const sendBtn = document.getElementById('mail-send-btn');
    const sendLabel = sendBtn.querySelector('.mail-btn-label');
    const alertBox = document.getElementById('mail-alert');
    const alertText = document.getElementById('mail-alert-text');
    const alertClose = document.getElementById('mail-alert-close');
    const overlay = document.getElementById('mail-success-overlay');
    const recipientEcho = document.getElementById('mail-success-recipient');
    const stayBtn = document.getElementById('mail-success-stay');
    const loader = document.getElementById('mail-preview-loader');
    const iframe = document.getElementById('mail-preview-iframe');

    const sendUrl = form.dataset.sendUrl;
    const proposalId = Number(form.dataset.proposalId);
    const initialBody = bodyInput.value;
    const sendLabelDefault = sendLabel.textContent;
    const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    /* ---------- Compteur de caractères ---------- */
    function updateCounter() {
        const length = bodyInput.value.length;
        counter.textContent = length + (length > 1 ? ' caractères' : ' caractère');
    }

    bodyInput.addEventListener('input', function () {
        updateCounter();
        document.querySelectorAll('.mail-chip.is-active').forEach(function (chip) {
            chip.classList.remove('is-active');
        });
    });
    updateCounter();

    /* ---------- Aperçu PDF : masquer le loader une fois chargé ---------- */
    if (iframe && loader) {
        iframe.addEventListener('load', function () {
            loader.classList.add('is-hidden');
        });
        // Filet de sécurité si l'évènement load n'est pas déclenché par le lecteur PDF
        setTimeout(function () {
            loader.classList.add('is-hidden');
        }, 6000);
    }

    /* ---------- Modèles rapides ---------- */
    const signature = initialBody.split('\n').slice(-3).join('\n');
    const clientLine = initialBody.split('\n')[0];

    const templates = {
        cordial: initialBody,
        court:
            clientLine + '\n\n' +
            'Comme convenu, veuillez trouver ci-joint notre proposition commerciale.\n' +
            'Je reste disponible pour en échanger quand vous le souhaitez.\n\n' +
            signature,
        relance:
            clientLine + '\n\n' +
            "Je me permets de revenir vers vous au sujet de la proposition commerciale que nous vous avons adressée.\n" +
            "Je vous la joins à nouveau pour plus de confort.\n\n" +
            "Avez-vous eu l'occasion d'en prendre connaissance ? Je serais ravi d'échanger sur les points à ajuster.\n\n" +
            signature,
        reset: initialBody
    };

    document.querySelectorAll('.mail-chip').forEach(function (chip) {
        chip.addEventListener('click', function () {
            const key = chip.dataset.template;
            if (!templates[key]) {
                return;
            }
            bodyInput.value = templates[key];
            updateCounter();
            document.querySelectorAll('.mail-chip').forEach(function (other) {
                other.classList.remove('is-active');
            });
            if (key !== 'reset') {
                chip.classList.add('is-active');
            }
            bodyInput.focus();
            bodyInput.setSelectionRange(0, 0);
        });
    });

    /* ---------- Bandeau d'erreur ---------- */
    function clearInvalidFields() {
        form.querySelectorAll('.is-invalid').forEach(function (element) {
            element.classList.remove('is-invalid');
        });
    }

    function hideError() {
        alertBox.hidden = true;
        clearInvalidFields();
    }

    function showError(message, field) {
        clearInvalidFields();
        alertText.textContent = message;
        alertBox.hidden = false;
        // Relance l'animation à chaque nouvelle erreur
        alertBox.classList.remove('is-shaking');
        void alertBox.offsetWidth;
        alertBox.classList.add('is-shaking');

        if (field) {
            (field.closest('.mail-input-wrap') || field).classList.add('is-invalid');
            field.focus();
        } else {
            alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    alertClose.addEventListener('click', hideError);

    [toInput, ccInput, subjectInput, bodyInput].forEach(function (field) {
        field.addEventListener('input', function () {
            (field.closest('.mail-input-wrap') || field).classList.remove('is-invalid');
        });
    });

    /* ---------- Validation côté client (le serveur revalide tout) ---------- */
    function validateForm() {
        const recipient = toInput.value.trim();
        if (!EMAIL_PATTERN.test(recipient)) {
            showError('Merci de saisir une adresse email valide pour le destinataire.', toInput);
            return false;
        }

        const invalidCc = ccInput.value
            .split(/[,;]/)
            .map(function (address) { return address.trim(); })
            .filter(function (address) { return address && !EMAIL_PATTERN.test(address); });
        if (invalidCc.length) {
            showError('Adresse en copie invalide : ' + invalidCc.join(', '), ccInput);
            return false;
        }

        if (!subjectInput.value.trim()) {
            showError("L'objet du mail ne peut pas être vide.", subjectInput);
            return false;
        }
        if (!bodyInput.value.trim()) {
            showError('Le message ne peut pas être vide.', bodyInput);
            return false;
        }
        return true;
    }

    /* ---------- Confettis ---------- */
    function launchConfetti() {
        const colors = ['#a8c47a', '#c2d97a', '#e6edd2', '#f39c12', '#27ae60', '#ffffff'];
        for (let i = 0; i < 60; i++) {
            const piece = document.createElement('span');
            piece.className = 'mail-confetti';
            piece.style.left = Math.random() * 100 + 'vw';
            piece.style.background = colors[Math.floor(Math.random() * colors.length)];
            piece.style.animationDuration = (2 + Math.random() * 2) + 's';
            piece.style.animationDelay = (Math.random() * 0.6) + 's';
            document.body.appendChild(piece);
            setTimeout(function () {
                piece.remove();
            }, 5000);
        }
    }

    function showSuccess(recipients) {
        const to = (recipients && recipients.to && recipients.to[0]) || toInput.value.trim();
        const ccCount = recipients && recipients.cc ? recipients.cc.length : 0;
        recipientEcho.textContent = to + (ccCount ? ' (+ ' + ccCount + ' en copie)' : '');
        overlay.hidden = false;
        launchConfetti();
    }

    /* ---------- Envoi ---------- */
    function getCsrf() {
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : '';
    }

    function setSending(isSending) {
        sendBtn.disabled = isSending;
        sendBtn.classList.toggle('is-sending', isSending);
        sendLabel.textContent = isSending ? 'Envoi en cours…' : sendLabelDefault;
    }

    // Traduit une réponse non-JSON (redirection de connexion, CSRF, erreur serveur) en message lisible
    function messageForUnexpectedResponse(response) {
        if (response.redirected) {
            return 'Votre session a expiré. Reconnectez-vous puis réessayez.';
        }
        if (response.status === 403) {
            return 'La page a expiré. Rechargez-la puis réessayez.';
        }
        return "Une erreur inattendue est survenue (code " + response.status + "). Veuillez réessayer.";
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (sendBtn.disabled) {
            return;
        }

        hideError();
        if (!validateForm()) {
            return;
        }

        setSending(true);
        try {
            const response = await fetch(sendUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrf()
                },
                body: JSON.stringify({
                    proposal_id: proposalId,
                    to: toInput.value.trim(),
                    cc: ccInput.value.trim(),
                    subject: subjectInput.value.trim(),
                    body: bodyInput.value
                })
            });

            const contentType = response.headers.get('Content-Type') || '';
            const data = contentType.includes('application/json') ? await response.json() : null;

            if (response.ok && data && data.success) {
                showSuccess(data.recipients);
            } else if (data && data.message) {
                showError(data.message);
            } else {
                showError(messageForUnexpectedResponse(response));
            }
        } catch (error) {
            showError('Impossible de joindre le serveur. Vérifiez votre connexion puis réessayez.');
        } finally {
            setSending(false);
        }
    });

    /* ---------- Fermeture de l'overlay ---------- */
    if (stayBtn) {
        stayBtn.addEventListener('click', function () {
            overlay.hidden = true;
        });
    }

    overlay.addEventListener('click', function (event) {
        if (event.target === overlay) {
            overlay.hidden = true;
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !overlay.hidden) {
            overlay.hidden = true;
        }
    });
});
