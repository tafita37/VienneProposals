INSERT INTO role (name) VALUES
('Commercial'),
('Gestionnaire de stock'),
('Administrateur');

INSERT INTO category (name) VALUES
('Portes intérieures'),
('Panneaux sandwich'),
('Peinture'),
('Électricité'),
('Quincaillerie');

INSERT INTO unit (name) VALUES
('pce'),
('m²'),
('fût'),
('pot'),
('m');

insert into admin_users (password, last_login, id, username, first_name, last_name, email) values(
'pbkdf2_sha256$1000000$N6AgkWkdPQ5n5SyN4ZeSpi$VBYnnahoZjJDAmfxvFvzfHvdKeaPLQAsffhCHxb9fYA=', '2026-04-13 17:08:43.36359+03', 1, 'admin', 'Ny Aina', 'Ny Aina', 'taf.rand37@gmail.com');

INSERT INTO product (designation, purchase_unit_price, sale_unit_price, coefficient, unit_id, category_id) VALUES
('Porte battante XL - Finition Chêne', 450, 585, 1, 1, 1),
('Porte battante XL - Finition Blanc', 420, 546, 1, 1, 1),
('Porte coulissante - Finition Chêne', 680, 884, 1, 1, 1),
('Porte coulissante - Finition Blanc', 620, 806, 1, 1, 1),
('Panneau cloisonnage 4cm - Blanc', 85, 110.5, 1, 2, 2),
('Panneau cloisonnage 6cm - Blanc', 105, 136.5, 1, 2, 2),
('Panneau cloisonnage 4cm - Gris', 90, 117, 1, 2, 2),
('Peinture murs - Gris clair (200L)', 180, 234, 1, 3, 3),
('Peinture murs - Blanc pur (200L)', 165, 214.5, 1, 3, 3),
('Peinture trim - Gris anthracite (5L)', 45, 58.5, 1, 4, 3),
('Goulotte électrique 40x40', 12, 15.6, 1, 5, 4),
('Prise double - Blanc', 22, 28.6, 1, 1, 4),
('Interrupteur simple - Blanc', 18, 23.4, 1, 1, 4),
('Poignée chrome XXL', 35, 45.5, 1, 1, 5),
('Charnière acier inox', 8, 10.4, 1, 1, 5);

INSERT INTO company_type (name) VALUES
('SARL'),
('SAS'),
('SA'),
('EURL'),
('Auto-entrepreneur');

INSERT INTO client (name, address, email, website_url, phone, is_company) VALUES
('Jean Dupont', '12 Rue de la Paix, 75002 Paris', 'contact@dupont-entreprise.fr', 'https://www.dupont-entreprise.fr', '+33 1 42 61 12 34', FALSE),
('Marie Martin', '25 Avenue Victor Hugo, 75116 Paris', 'bonjour@martin-design.com', 'https://www.martin-design.com', '+33 1 45 00 23 45', FALSE),
('Pierre Bernard', '8 Place Bellecour, 69002 Lyon', 'info@bernard-conseil.fr', 'https://www.bernard-conseil.fr', '+33 4 78 37 45 67', FALSE),
('Sophie Petit', '35 Rue Saint-Ferréol, 13001 Marseille', 'contact@petit-import.com', 'https://www.petit-import.com', '+33 4 91 54 67 89', FALSE),
('Thomas Robert', '42 Rue Nationale, 59000 Lille', 'hello@robert-tech.fr', 'https://www.robert-tech.fr', '+33 3 20 15 78 90', FALSE),
('SARL Richard & Fils', '5 Rue de la République, 69001 Lyon', 'contact@richard-sante.fr', 'https://www.richard-sante.fr', '+33 4 72 10 34_56', TRUE),
('SAS Simon Distribution', '18 Rue du Faubourg Saint-Honoré, 75008 Paris', 'info@simon-luxe.com', 'https://www.simon-luxe.com', '+33 1 53 43 67 89', TRUE),
('SA Michel Aérospatiale', '3 Place du Capitole, 31000 Toulouse', 'contact@michel-aero.fr', 'https://www.michel-aero.fr', '+33 5 61 23 45 67', TRUE),
('EURL Laurent Vignobles', '27 Rue de la Liberté, 21000 Dijon', 'bonjour@laurent-vins.fr', 'https://www.laurent-vins.fr', '+33 3 80 30 67 89', TRUE),
('Dubois Technologies', '15 Quai des Belges, 34000 Montpellier', 'contact@dubois-tech.com', 'https://www.dubois-tech.com', '+33 4 67 12 34 56', TRUE);

INSERT INTO individual (first_name, last_name, birth_date, id_card_number, client_id) VALUES
('Jean', 'Dupont', '1975-03-15', 'CNI123456789', 1),
('Marie', 'Martin', '1982-07-22', 'CNI987654321', 2),
('Pierre', 'Bernard', '1968-11-30', 'CNI456789123', 3),
('Sophie', 'Petit', '1990-05-18', 'CNI789123456', 4),
('Thomas', 'Robert', '1985-09-08', 'CNI321654987', 5);

INSERT INTO company (name, registration_number, tax_identification_number, created_at, company_type_id, client_id) VALUES
('SARL Richard & Fils', 'RCS LYON 123 456 789', 'TVA FR12345678901', '2018-04-12', 1, 6),
('SAS Simon Distribution', 'RCS PARIS 987 654 321', 'TVA FR98765432109', '2015-09-23', 2, 7),
('SA Michel Aérospatiale', 'RCS TOULOUSE 456 789 123', 'TVA FR45678912345', '2010-02-01', 3, 8),
('EURL Laurent Vignobles', 'RCS DIJON 789 123 456', 'TVA FR78912345678', '2019-11-15', 4, 9),
('Dubois Technologies', 'RCS MONTPELLIER 321 654 987', 'TVA FR32165498701', '2020-06-30', 5, 10);

INSERT INTO products_coefficient_history (coefficient) VALUES (1.3);

-- Commercial

-- Login commercial
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Authentification', '1', 'url', 'Pour accéder au login côté commercial voici le chemin /auth/login_page/. Ce chemin s ouvre automatiquement si vous n êtes pas encore connecté.'),
('commercial', 'Authentification', '2', 'navigation', 'Il faut ensuite renseigner l identifiant et le mot de passe dans les champs indiqués et cliquer sur le bouton "Connexion"'),
('commercial', 'Authentification', null, 'erreur', 'Si les identifiants/mot de passe sont incorrects, un message d erreur s affichera. Il faudra alors vérifier les informations saisies et réessayer.'),
('commercial', 'Authentification', null, 'erreur', 'Si le compte est bloqué, il faudra contacter l administrateur pour le débloquer.'),
('commercial', 'Authentification', null, 'erreur', 'Si le compte est inactif, il faudra contacter l administrateur pour l activer.');

-- Mot de passe oublié
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Authentification', '1', 'navigation', 'En cas de mot de passe oublié il faut cliquer sur le lien juste en dessous du bouton "Connexion" : "Mot de passe oublié ?".'),
('commercial', 'Authentification', '2', 'url', 'Vous serez redirigé vers la page /auth/forgot_password_page/ pour réinitialiser votre mot de passe.'),
('commercial', 'Authentification', '3', 'navigation', 'Il faudra ensuite renseigner l adresse email associée à votre compte et cliquer sur le bouton "Envoyer le lien".'),
('commercial', 'Authentification', '4', 'navigation', 'Vous recevrez un email contenant un lien valide 7 jours pour réinitialiser votre mot de passe. Cliquez sur ce lien pour accéder à la page de réinitialisation.'),
('commercial', 'Authentification', '5', 'navigation', 'Sur la page de réinitialisation, il faudra renseigner le nouveau mot de passe et le confirmer en le saisissant à nouveau. Cliquez ensuite sur le bouton "Mettre à jour le mot de passe".'),
('commercial', 'Authentification', null, 'erreur', 'Si le lien de réinitialisation est expiré, il faudra recommencer la procédure depuis le début en cliquant sur "Mot de passe oublié ?".'),
('commercial', 'Authentification', null, 'erreur', 'Si l adresse email saisie n est pas associée à un compte, aucun email de réinitialisation ne sera envoyé. Il faudra vérifier l adresse email et réessayer.'),
('commercial', 'Authentification', null, 'erreur', 'Si le nouveau mot de passe ne respecte pas les critères de sécurité (longueur minimale, complexité, etc.), un message d erreur s affichera. Il faudra choisir un mot de passe conforme aux exigences et réessayer.');

-- Dashboard
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Dashboard', null, 'url', 'Après la connexion, vous serez redirigé vers le tableau de bord du commercial. Sur le menu horizontal, il suffit de cliquer sur "Dashboard". Le chemin est /com/dashboard_user_page/.'),
('commercial', 'Dashboard', '2', 'navigation', 'Le tableau de bord affiche le nombre de propositions crées, validées, en attente, la marge brute générée par mois et par année du commercial connecté sous forme de graphiques. Juste en dessous il pourra également voir la marge brute cumulée pour l annéé et le mois de l année ou il a été le plus performant. Vous pouvez naviguer vers différentes sections en utilisant le menu latéral.'),
('commercial', 'Dashboard', null, 'erreur', 'Si vous rencontrez des problèmes pour accéder au tableau de bord, assurez-vous que votre compte est actif et que vous avez les permissions nécessaires. Contactez l administrateur si le problème persiste.');

-- Création de proposition commerciale
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Création de proposition commerciale', '1', 'url', 'Pour créer une nouvelle proposition commerciale, dans le menu latéral vous pouvez soit cliquer sur "Catalogue" qui va vous rediriger vers /com/catalog_page/ soit directement sur "Nouvelle Proposition" qui va vous rediriger vers /com/new_proposition_page/.'),
('commercial', 'Création de proposition commerciale', '2.1', 'navigation', 'Si vous cliquez sur "Catalogue", vous serez redirigé vers la page /com/catalogue_page/ où vous pourrez consulter les produits disponibles.'),
('commercial', 'Création de proposition commerciale', '2.1.1', 'navigation', 'Vous pourrez alors accès à la liste des produits avec la possibilité de filtrer par catégorie ou de rechercher un produit spécifique.'),
('commercial', 'Création de proposition commerciale', '2.1.2', 'navigation', 'Vous devrez ensuite choisir les produits que vous souhaitez inclure dans la proposition en indiquant des coefficients et quantités par produit et éventuellement des explications supplémentaires.'),
('commercial', 'Création de proposition commerciale', '2.1.3', 'navigation', 'Après avoir sélectionné les produits, cliquez sur le bouton "Créer une proposition" et vous serez ensuite redirigé vers /com/create_proposal_page/ pour la suite'),
('commercial', 'Création de proposition commerciale', '2.2', 'navigation', 'Si vous cliquez sur "Nouvelle Proposition", vous serez redirigé vers la page /com/create_proposal_page/ pour commencer la création d une nouvelle proposition commerciale.'),
('commercial', 'Création de proposition commerciale', '2.2.1', 'navigation', 'Vous devrez ensuite choisir un client dans la liste déroulante et vous avez la possibilité de créer un nouveau client avec le bouton "+ Client" ou d en modifier après avoir sélectionner avec le bouton "Modifier".'),
('commercial', 'Création de proposition commerciale', '2.2.1.1', 'navigation', 'Si vous cliquez sur "+ Client", vous serez redirigé vers la page /com/new_client_user_page/ pour créer un nouveau client. Vous devrez remplir les informations nécéssaires et séléctionner si le client est B2B ou B2C et remplir les informations correspondantes. Après avoir rempli toutes les informations, cliquez sur le bouton "Enregistrer" pour sauvegarder le client ou "Retour à la proposition" pour annuler et en revenir à la proposition.'),
('commercial', 'Création de proposition commerciale', '2.2.2', 'navigation', 'Il faudra ensuite remplir d autres informations comme le nom du projet, l adresse d installation, ce qui n est pas compris dans le service, les conditions générales de ventes et les dates de proposition et d expiration'),
('commercial', 'Création de proposition commerciale', '2.2.3', 'navigation', 'En scrollant plus bas, vous aurez un récapitulatif des produits choisis par catégorie, le total des achats ainsi que la possibilité d en ajouter d autre directement en sélectionnant une catégorie dans la liste déroulante, un produit, indiquer la quantité et le coefficient et cliquer sur "+Ajouter"'),
('commercial', 'Création de proposition commerciale', '2.2.4', 'navigation', 'Après avoir remplis toutes les informations concernant votre proposition, vous trouverez tout en bas un bouton "Apperçu et Valider", cliquez dessus et vous serez redirigé vers /com/preview_proposition_page/ pour avoir un apperçu de votre proposition et pouvoir la valider.'),
('commercial', 'Création de proposition commerciale', '2.2.5', 'navigation', 'En scrollant tout en bas on aura 3 boutons "<- Retour" pour modifier en cas d erreur, "Enregistrer en brouillon" en cas de possible modification dans le futur et "Valider" pour valider la proposition. Vous pouvez également télécharger l apperçu en PDF avec le bouton "Télécharger PDF" si besoin'),
('commercial', 'Création de proposition commerciale', null, 'erreur', 'Chaque erreur sera affiché de manière très explicite lors de la création : ex : Quantité négative, information manquante, etc.. Si une erreur vous semble inconnu n hesitez pas à contacter l administrateur du CRM');

-- Liste des propositions
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Liste des propositions', '1', 'url', 'Pour accéder à la liste des propositions commerciales, dans le menu latéral cliquez sur "Propositions" et vous serez redirigé vers /com/propositions_page/.'),
('commercial', 'Liste des propositions', '2', 'navigation', 'La liste des propositions affiche toutes les propositions créées par le commercial connecté (numéro, client, date de création, date d expiration, montant TTC, Statut (validé/brouillon), une colonne action pour voir/modifier (voir si la proposition est validée, modifier si encore brouillon)). Vous pouvez filtrer les propositions par statut (en attente, validée, rejetée) et rechercher les propositions d un client en en sélectionnant un dans la liste déroulante.'),
('commercial', 'Liste des propositions', null, 'navigation', 'Cliquez sur le bouton "Voir" dans la colonne action pour accéder au détail de la proposition sur /com/proposition_detail/?proposal_id=<proposal_id>. Vous pourrez télécharger en PDF la proposition en cliquant sur le bouton "Télécharger PDF" juste en dessous de la proposition');

-- Modification de proposition
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Modification de proposition', '1', 'url', 'Pour modifier une proposition commerciale, accédez à la liste des propositions sur /com/propositions_page/ et cliquez sur le bouton "Modifier" dans la colonne action pour la proposition que vous souhaitez modifier. Vous serez redirigé vers /com/edit_draft_proposition_page/?proposal_id=<proposal_id>. La page ressemblera exactement à la page de création de proposition, mais avec les informations pré-remplies pour la proposition sélectionnée. Le processus est le même que pour la création de proposition, cliquez sur "Apperçu et Valider" une fois satisfait et vous serez redirigé vers la page de validation /com/preview_proposition_page_edit/ et vous pourrez valider ou enregistrer en brouillon et même télécharger en pdf selon vos préférences.'),
('commercial', 'Modification de proposition', '2', 'navigation', 'Sur la page de modification, vous pourrez mettre à jour les informations de la proposition, ajouter ou supprimer des produits, ajuster les quantités et coefficients, et modifier les détails du client si nécessaire.');

-- Changer mot de passe
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Changer le mot de passe', '1', 'url', 'Pour changer votre mot de passe, accédez à la section "Modifier mot de passe" dans le menu latéral. Vous serez redirigé vers /auth/change_password_page/.'),
('commercial', 'Changer le mot de passe', '2', 'navigation', 'Renseignez votre mot de passe actuel, puis saisissez votre nouveau mot de passe et confirmez-le. Cliquez sur "Enregistrer" pour enregistrer les modifications.'),
('commercial', 'Changer le mot de passe', null, 'erreur', 'Si le mot de passe actuel est incorrect ou si le nouveau mot de passe ne respecte pas les critères de sécurité, un message d erreur s affichera. Veuillez vérifier les informations saisies et réessayer.');

-- Déconnexion
INSERT INTO help_document(level, title, step, type, content) VALUES
('commercial', 'Déconnexion', '1', 'url', 'Pour vous déconnecter de votre compte commercial, cliquez sur le bouton "Déconnexion" dans le menu latéral. Vous serez redirigé vers la page de connexion /auth/login_page/.'),
('commercial', 'Déconnexion', null, 'navigation', 'Assurez-vous de sauvegarder toutes les modifications avant de vous déconnecter pour éviter toute perte de données.');


-- Administrateur
-- Login Administrateur
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Authentification', '1', 'url', 'Pour accéder au login côté admin voici le chemin /admin/login_admin_page/.'),
('admin', 'Authentification', '2', 'navigation', 'Il faut ensuite renseigner l identifiant et le mot de passe dans les champs indiqués et cliquer sur le bouton "Connexion"'),
('admin', 'Authentification', null, 'erreur', 'Si les identifiants/mot de passe sont incorrects, un message d erreur s affichera. Il faudra alors vérifier les informations saisies et réessayer.'),
('admin', 'Authentification', null, 'erreur', 'Si le compte est bloqué, il faudra contacter l administrateur pour le débloquer.'),
('admin', 'Authentification', null, 'erreur', 'Si le compte est inactif, il faudra contacter l administrateur pour l activer.');

-- Mot de passe oublié
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Authentification', '1', 'navigation', 'En cas de mot de passe oublié il faut cliquer sur le lien juste en dessous du bouton "Connexion" : "Mot de passe oublié ?".'),
('admin', 'Authentification', '2', 'url', 'Vous serez redirigé vers la page /admin/forgot_password_page/ pour réinitialiser votre mot de passe.'),
('admin', 'Authentification', '3', 'navigation', 'Il faudra ensuite renseigner l adresse email associée à votre compte et cliquer sur le bouton "Envoyer le lien".'),
('admin', 'Authentification', '4', 'navigation', 'Vous recevrez un email contenant un lien valide 7 jours pour réinitialiser votre mot de passe. Cliquez sur ce lien pour accéder à la page de réinitialisation.'),
('admin', 'Authentification', '5', 'navigation', 'Sur la page de réinitialisation, il faudra renseigner le nouveau mot de passe et le confirmer en le saisissant à nouveau. Cliquez ensuite sur le bouton "Mettre à jour le mot de passe".'),
('admin', 'Authentification', null, 'erreur', 'Si le lien de réinitialisation est expiré, il faudra recommencer la procédure depuis le début en cliquant sur "Mot de passe oublié ?".'),
('admin', 'Authentification', null, 'erreur', 'Si l adresse email saisie n est pas associée à un compte, aucun email de réinitialisation ne sera envoyé. Il faudra vérifier l adresse email et réessayer.'),
('admin', 'Authentification', null, 'erreur', 'Si le nouveau mot de passe ne respecte pas les critères de sécurité (longueur minimale, complexité, etc.), un message d erreur s affichera. Il faudra choisir un mot de passe conforme aux exigences et réessayer.');

-- Dashboard
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Dashboard', null, 'url', 'Après la connexion, vous serez redirigé vers le tableau de bord de l administrateur. Sur le menu horizontal, il suffit de cliquer sur "Dashboard". Le chemin est /admin/dashboard_page/.'),
('admin', 'Dashboard', '2', 'navigation', 'Le tableau de bord affiche les propositions crées et la marge brute annuelle générées par commercial avec possibilité de filtrer par année. Un graphe est également disponible pour visualiser les marges brutes générés pour chaque commercial et pouvoir les comparer. Juste en dessous, un graphe affichant la marge brute mensuelle par année généré par Vienne Agencement et filtrable par année ainsi que la marge brute cumulée annuelle et le mois ou de l année ou Vienne Agencement a été le plus performant.');

-- CRUD Client
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'CRUD Client', '1', 'url', 'Pour accéder à la gestion des clients, dans le menu latéral cliquez sur "Clients" et vous serez redirigé vers /admin/client/list/.'),
('admin', 'CRUD Client', '2', 'navigation', 'La liste des clients affiche tous les clients enregistrés dans le système avec leurs informations principales.'),
('admin', 'CRUD Client', '3', 'navigation', 'Pour ajouter un nouveau client, cliquez sur le bouton "+ Ajouter un client" en haut de la page. Vous serez redirigé vers /admin/client/new/ où vous devrez remplir les informations nécéssaires et séléctionner si le client est B2B ou B2C et remplir les informations correspondantes.'),
('admin', 'CRUD Client', '4', 'navigation', 'Pour modifier un client existant, cliquez sur l icône de modification ressemblant à un crayon dans la colonne "Actions" pour le client que vous souhaitez mettre à jour. Vous serez redirigé vers /admin/client/edit/<client_id>/ où vous pourrez modifier les informations du client.'),
('admin', 'CRUD Client', '5', 'navigation', 'Pour supprimer un client, cliquez sur l icône ressemblant à une corbeille dans la colonne action pour le client que vous souhaitez supprimer. Une confirmation sera demandée avant la suppression définitive du client.');

-- CRUD Catégorie
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'CRUD Catégorie', '1', 'url', 'Pour accéder à la gestion des catégories de produits, dans le menu latéral cliquez sur "Catégories" et vous serez redirigé vers /admin/category/list/.'),
('admin', 'CRUD Catégorie', '2', 'navigation', 'La liste des catégories affiche toutes les catégories de produits enregistrées dans le système.'),
('admin', 'CRUD Catégorie', '3', 'navigation', 'Pour ajouter une nouvelle catégorie, cliquez sur le bouton "+ Ajouter une catégorie" en haut de la page. Une fenêtre modal s ouvrira pour vous permettre d indiquer le nom de la catégorie. Cliquez sur le bouton "Enregistrer" pour sauvegarder la nouvelle catégorie ou sur le bouton Annuler pour fermer la fenêtre sans enregistrer.'),
('admin', 'CRUD Catégorie', '4', 'navigation', 'Pour modifier une catégorie existante, cliquez sur l icône de modification ressemblant à un crayon dans la colonne "Actions" pour la catégorie que vous souhaitez mettre à jour. Une fenêtre modal s ouvrira pour vous permettre de modifier le nom de la catégorie. Cliquez sur le bouton "Enregistrer" pour sauvegarder les modifications ou sur le bouton Annuler pour fermer la fenêtre sans enregistrer.'),
('admin', 'CRUD Catégorie', '5', 'navigation', 'Pour supprimer une catégorie, cliquez sur l icône ressemblant à une corbeille dans la colonne action pour la catégorie que vous souhaitez supprimer. Une confirmation sera demandée avant la suppression définitive de la catégorie.');

-- CRUD Produit
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'CRUD Produit', '1', 'url', 'Pour accéder à la gestion des produits, dans le menu latéral cliquez sur "Produits" et vous serez redirigé vers /admin/product/list/.'),
('admin', 'CRUD Produit', '2', 'navigation', 'La liste des produits affiche tous les produits enregistrés dans le système avec leurs informations principales. Il vous est possible de filtrer les produits par catégorie et de rechercher un produit spécifique en utilisant la barre de recherche.'),
('admin', 'CRUD Produit', '3', 'navigation', 'Pour ajouter un nouveau produit, cliquez sur le bouton "+ Ajouter un produit" en haut de la page. Une fenêtre modal s ouvrira pour vous permettre de remplir les informations nécéssaires pour le produit (désignation, catégorie(s), unité de mesure, prix unitaire d achat, coefficient, prix unitaire de vente). Cliquez sur le bouton "Enregistrer" pour sauvegarder le nouveau produit ou sur le bouton Annuler pour fermer la fenêtre sans enregistrer.'),
('admin', 'CRUD Produit', '4', 'navigation', 'Pour modifier un produit existant, cliquez sur l icône de modification ressemblant à un crayon dans la colonne "Actions" pour le produit que vous souhaitez mettre à jour. Une fenêtre modal s ouvrira pour vous permettre de modifier les informations du produit. Cliquez sur le bouton "Enregistrer" pour sauvegarder les modifications ou sur le bouton Annuler pour fermer la fenêtre sans enregistrer.'),
('admin', 'CRUD Produit', '5', 'navigation', 'Pour supprimer un produit, cliquez sur l icône ressemblant à une corbeille dans la colonne action pour le produit que vous souhaitez supprimer. Une confirmation sera demandée avant la suppression définitive du produit.'),
('admin', 'CRUD Produit', null, 'navigation', 'Il est également possible d appliquer un coefficient global à tout les produits en cliquant sur le bouton "Modifier le coefficient" en haut de la page. Une fenêtre modal s ouvrira pour vous permettre d indiquer le coefficient à appliquer. Cliquez sur le bouton "Valider les modifications" pour mettre à jour les prix de vente de tous les produits en fonction du coefficient indiqué ou sur le bouton Annuler pour fermer la fenêtre sans appliquer de coefficient. Le coefficient global est affiché au dessus de la liste des produits.');

-- CRUD Utilisateur
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'CRUD Utilisateur', '1', 'url', 'Pour accéder à la gestion des utilisateurs, dans le menu latéral cliquez sur "Utilisateurs" et vous serez redirigé vers /admin/user/list/.'),
('admin', 'CRUD Utilisateur', '2', 'navigation', 'La liste des utilisateurs affiche tous les utilisateurs enregistrés dans le système avec leurs informations principales.'),
('admin', 'CRUD Utilisateur', '3', 'navigation', 'Pour ajouter un nouvel utilisateur, cliquez sur le bouton "+ Ajouter un utilisateur" en haut de la page. Vous serez redirigé vers /admin/user/new/. Vous devrez remplir les informations nécéssaires pour l utilisateur (nom, prénom, nom d utilisateur, email). Cliquez sur le bouton "Enregistrer" pour sauvegarder le nouvel utilisateur ou sur le bouton Annuler pour revenir à la liste des utilisateurs sans enregistrer. Si le mail est valide, un mail sera envoyé à l utilisateur pour lui permettre de créer son mot de passe et se connecter.'),
('admin', 'CRUD Utilisateur', '4', 'navigation', 'Pour modifier un utilisateur existant, cliquez sur le bouton "Modifier" dans la colonne "Actions" pour l utilisateur que vous souhaitez mettre à jour. Une fenêtre modal s ouvrira pour vous permettre de modifier les informations de l utilisateur. Cliquez sur le bouton "Enregistrer" pour sauvegarder les modifications ou sur le bouton Annuler pour fermer la fenêtre sans enregistrer.'),
('admin', 'CRUD Utilisateur', '5', 'navigation', 'Pour supprimer un utilisateur, cliquez sur l icône ressemblant à une corbeille dans la colonne action pour l utilisateur que vous souhaitez supprimer. Une confirmation sera demandée avant la suppression définitive de l utilisateur.');

-- Import excel
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Import Excel', '1', 'url', 'Pour importer des produits depuis un fichier Excel, dans le menu latéral cliquez sur "Import Excel" et vous serez redirigé vers /admin/import_page/.'),
('admin', 'Import Excel', '2', 'navigation', 'Avant d importer, vous devrez choisir la catégorie cible si il s agit d une catégorie existante en cochant catégorie existante et en choisissant dans la liste déroulante. Si il s agit d une nouvelle catégorie, cochez "Nouvelle catégorie" et indiquez le nom de la nouvelle catégorie. Si vous n indiquez aucun nom l application lira la catégorie dans le fichier Excel.'),
('admin', 'Import Excel', '2.1', 'navigation', 'Si il s agit d une catégorie existante, séléctionnez si il s agit de modification de produit existant en cochant "Produits existants", ou de nouveau produits en cochant "Nouveaux Produits"'),
('admin', 'Import Excel', '3', 'navigation', 'Cliquez sur le bouton "Sélectionner un fichier", séléctionnez le fichier à importer et importez le. Un message de confirmation s affichera une fois l importation terminée avec succès ou en cas d erreurs.'),
('admin', 'Import Excel', null, 'erreur', 'Si le fichier Excel ne respecte pas le format attendu ou contient des erreurs, un message d erreur détaillé s affichera indiquant ligne par ligne les erreurs.');

-- Changer mot de passe
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Changer le mot de passe', '1', 'url', 'Pour changer votre mot de passe, accédez à la section "Modifier mot de passe" dans le menu latéral. Vous serez redirigé vers /admin/change_password_page/.'),
('admin', 'Changer le mot de passe', '2', 'navigation', 'Renseignez votre mot de passe actuel, puis saisissez votre nouveau mot de passe et confirmez-le. Cliquez sur "Enregistrer" pour enregistrer les modifications.'),
('admin', 'Changer le mot de passe', null, 'erreur', 'Si le mot de passe actuel est incorrect ou si le nouveau mot de passe ne respecte pas les critères de sécurité, un message d erreur s affichera. Veuillez vérifier les informations saisies et réessayer.');

-- Déconnexion
INSERT INTO help_document(level, title, step, type, content) VALUES
('admin', 'Déconnexion', '1', 'url', 'Pour vous déconnecter de votre compte admin, cliquez sur le bouton "Déconnexion" dans le menu latéral.'),
('admin', 'Déconnexion', null, 'navigation', 'Assurez-vous de sauvegarder toutes les modifications avant de vous déconnecter pour éviter toute perte de données.');