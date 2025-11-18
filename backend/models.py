from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """Modèle utilisateur pour le système d'authentification"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    organization = db.Column(db.String(100))  # CSC, MTDPCE, etc.
    role = db.Column(db.String(50), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'organization': self.organization,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Media(db.Model):
    """Modèle pour les médias surveillés"""
    __tablename__ = 'medias'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    url_base = db.Column(db.String(500))
    type = db.Column(db.String(50))  # web, social_media
    couleur = db.Column(db.String(7), default='#3B82F6')  # Hex color
    icon = db.Column(db.String(50))  # Nom de l'icône
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    articles = db.relationship('Article', backref='media', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='media', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url_base': self.url_base,
            'type': self.type,
            'couleur': self.couleur,
            'icon': self.icon,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_articles': self.articles.count()
        }


class Article(db.Model):
    """Modèle pour les articles collectés"""
    __tablename__ = 'articles'
    
    id = db.Column(db.String(255), primary_key=True)  # ID du CSV
    media_id = db.Column(db.Integer, db.ForeignKey('medias.id', ondelete='CASCADE'), nullable=False, index=True)
    categorie_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), index=True)
    
    titre = db.Column(db.String(500), nullable=False)
    contenu = db.Column(db.Text)
    url = db.Column(db.String(1000), index=True)
    date = db.Column(db.DateTime, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    engagement = db.relationship('Engagement', backref='article', uselist=False, cascade='all, delete-orphan')
    categorie = db.relationship('Categorie', backref='articles')
    
    def to_dict(self):
        return {
            'id': self.id,
            'media_id': self.media_id,
            'media_name': self.media.name if self.media else None,
            'categorie': self.categorie.nom if self.categorie else None,
            'titre': self.titre,
            'contenu': self.contenu,
            'url': self.url,
            'date': self.date.isoformat() if self.date else None,
            'engagement': self.engagement.to_dict() if self.engagement else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Categorie(db.Model):
    """Modèle pour les catégories d'articles"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    couleur = db.Column(db.String(7), default='#6B7280')  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'couleur': self.couleur,
            'total_articles': len(self.articles)
        }


class Engagement(db.Model):
    """Modèle pour les métriques d'engagement"""
    __tablename__ = 'engagements'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(255), db.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    likes = db.Column(db.Integer, default=0)
    commentaires = db.Column(db.Integer, default=0)
    partages = db.Column(db.Integer, default=0)
    type_source = db.Column(db.String(50))  # article, post_social
    plateforme = db.Column(db.String(50))  # web, facebook, twitter
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'likes': self.likes,
            'commentaires': self.commentaires,
            'partages': self.partages,
            'total': self.likes + self.commentaires + self.partages,
            'type_source': self.type_source,
            'plateforme': self.plateforme
        }


class Alert(db.Model):
    """Modèle pour le système d'alertes"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('medias.id', ondelete='CASCADE'), nullable=False, index=True)
    
    type = db.Column(db.String(100), nullable=False)  # Pic d'activité, Contenu sensible, etc.
    severite = db.Column(db.String(20), nullable=False)  # critical, high, medium, low
    titre = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_resolved = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'media_id': self.media_id,
            'media_name': self.media.name if self.media else None,
            'type': self.type,
            'severite': self.severite,
            'titre': self.titre,
            'message': self.message,
            'date': self.date.isoformat() if self.date else None,
            'is_resolved': self.is_resolved
        }


class MediaStats(db.Model):
    """Modèle pour les statistiques quotidiennes des médias"""
    __tablename__ = 'media_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('medias.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Métriques calculées
    total_articles = db.Column(db.Integer, default=0)
    total_likes = db.Column(db.Integer, default=0)
    total_commentaires = db.Column(db.Integer, default=0)
    total_partages = db.Column(db.Integer, default=0)
    total_engagement = db.Column(db.Integer, default=0)
    influence_score = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    media = db.relationship('Media', backref='stats')
    
    # Index composite pour éviter les doublons
    __table_args__ = (
        db.UniqueConstraint('media_id', 'date', name='unique_media_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'media_id': self.media_id,
            'media_name': self.media.name if self.media else None,
            'date': self.date.isoformat(),
            'total_articles': self.total_articles,
            'total_engagement': self.total_engagement,
            'influence_score': self.influence_score,
            'metrics': {
                'likes': self.total_likes,
                'commentaires': self.total_commentaires,
                'partages': self.total_partages
            }
        }
