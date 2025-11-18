import { useNavigate } from 'react-router-dom';
import { Activity, TrendingUp, Shield, BarChart3, Users, Globe } from 'lucide-react';
import { useEffect, useRef } from 'react';
import './Home.css';

function Home() {
  const navigate = useNavigate();
  const partnersTrackRef = useRef(null);

  useEffect(() => {
    const track = partnersTrackRef.current;
    if (!track) return;

    const updateScale = () => {
      const items = track.querySelectorAll('.partner-item');
      const viewportCenter = window.innerWidth / 2;

      items.forEach((item) => {
        const rect = item.getBoundingClientRect();
        const itemCenter = rect.left + rect.width / 2;
        const distanceFromCenter = Math.abs(viewportCenter - itemCenter);
        const maxDistance = window.innerWidth / 2;
        
        // Calculer le scale basé sur la distance du centre
        // Plus proche du centre = plus grand (max 1.3), plus loin = plus petit (min 0.75)
        const scale = Math.max(0.75, Math.min(1.3, 1.3 - (distanceFromCenter / maxDistance) * 0.55));
        const opacity = Math.max(0.5, Math.min(1, 1 - (distanceFromCenter / maxDistance) * 0.5));
        
        item.style.transform = `scale(${scale})`;
        item.style.opacity = opacity;
        
        // Appliquer le filtre grayscale basé sur la distance
        const img = item.querySelector('img');
        const span = item.querySelector('span');
        if (img) {
          if (scale > 1.1) {
            img.style.filter = 'grayscale(0%)';
            if (span) span.style.color = '#3b82f6';
          } else {
            img.style.filter = 'grayscale(100%)';
            if (span) span.style.color = '#64748b';
          }
        }
      });
    };

    // Mettre à jour toutes les 50ms pour une animation fluide
    const interval = setInterval(updateScale, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="home-container">
      <div className="home-content">
        {/* Header and Hero as background text */}
        <div className="page-header-section">
          <div className="logo-section">
            <img 
              src="/imageonline-co-pixelated-removebg-preview.png" 
              alt="CSC Logo" 
              className="home-logo-image"
            />
            <div className="header-text">
              <h1>MÉDIA-SCAN</h1>
              <p className="tagline">Système Intelligent d'Observation et d'Analyse des Médias au Burkina Faso</p>
            </div>
          </div>
          
          <div className="hero-text">
            <h2>Surveillance et Analyse Intelligente du Paysage Médiatique</h2>
            <p className="hero-description">
              Une plateforme d'intelligence artificielle pour le Conseil Supérieur de la Communication (CSC) 
              permettant la collecte automatique, l'analyse thématique et la mesure d'influence des médias burkinabè.
            </p>
          </div>
        </div>

        {/* Features Grid */}
        <section className="features-grid">
          <div className="feature-card">
            <Globe className="feature-icon" size={32} />
            <h3>Collecte Automatique</h3>
            <p>Surveillance en temps réel de plus de 100 médias burkinabè en ligne</p>
          </div>

          <div className="feature-card">
            <BarChart3 className="feature-icon" size={32} />
            <h3>Analyse Thématique</h3>
            <p>Classification automatique par IA : politique, économie, sécurité, santé, culture, sport</p>
          </div>

          <div className="feature-card">
            <TrendingUp className="feature-icon" size={32} />
            <h3>Mesure d'Influence</h3>
            <p>Calcul de scores d'audience et d'engagement pour chaque média</p>
          </div>

          <div className="feature-card">
            <Shield className="feature-icon" size={32} />
            <h3>Détection de Contenus</h3>
            <p>Identification automatique des contenus sensibles et désinformation</p>
          </div>

          <div className="feature-card">
            <Users className="feature-icon" size={32} />
            <h3>Contrôle Réglementaire</h3>
            <p>Vérification du respect des obligations et grilles de programmes</p>
          </div>

          <div className="feature-card">
            <Activity className="feature-icon" size={32} />
            <h3>Rapports en Temps Réel</h3>
            <p>Dashboard interactif avec visualisations et export de rapports</p>
          </div>
        </section>

        {/* Mission Section */}
        <section className="mission-section">
          <h2>Notre Mission</h2>
          <p className="mission-text">
            MÉDIA-SCAN transforme la surveillance médiatique au Burkina Faso en garantissant une 
            transparence objective du paysage médiatique burkinabè pour renforcer la confiance du public. 
            La plateforme mesure l'impact réel des médias et leur contribution au débat démocratique 
            grâce à des données fiables. En automatisant la régulation, nous optimisons le travail 
            du CSC grâce à l'intelligence artificielle pour une régulation plus efficace et réactive.
          </p>
        </section>

        {/* Stats Section */}
        <section className="stats-section">
          <div className="stat-item">
            <h3>100+</h3>
            <p>Médias surveillés</p>
          </div>
          <div className="stat-item">
            <h3>1000+</h3>
            <p>Contenus/jour</p>
          </div>
          <div className="stat-item">
            <h3>6</h3>
            <p>Catégories thématiques</p>
          </div>
          <div className="stat-item">
            <h3>24/7</h3>
            <p>Surveillance continue</p>
          </div>
        </section>

        {/* Partners Section */}
        <section className="partners-section">
          <h3>Nos Partenaires</h3>
          <div className="partners-scroll">
            <div className="partners-track" ref={partnersTrackRef}>
              <div className="partner-item">
                <img src="/logos/csc-logo.png" alt="CSC" />
                <span>CSC</span>
              </div>
              <div className="partner-item">
                <img src="/logos/mtdpce-logo.png" alt="MTDPCE" />
                <span>MTDPCE</span>
              </div>
              <div className="partner-item">
                <img src="/logos/citadel-logo.png" alt="CITADEL" />
                <span>CITADEL</span>
              </div>
              <div className="partner-item">
                <img src="/logos/lefaso-logo.png" alt="Lefaso.net" />
                <span>Lefaso.net</span>
              </div>
              <div className="partner-item">
                <img src="/logos/fasopresse-logo.png" alt="FasoPresse" />
                <span>FasoPresse</span>
              </div>
              <div className="partner-item">
                <img src="/logos/sidwaya-logo.png" alt="Sidwaya" />
                <span>Sidwaya</span>
              </div>
              <div className="partner-item">
                <img src="/logos/observateur-logo.png" alt="L'Observateur Paalga" />
                <span>L'Observateur Paalga</span>
              </div>
              <div className="partner-item">
                <img src="/logos/aib-logo.png" alt="AIB" />
                <span>AIB</span>
              </div>
              {/* Duplicate pour loop continu */}
              <div className="partner-item">
                <img src="/logos/csc-logo.png" alt="CSC" />
                <span>CSC</span>
              </div>
              <div className="partner-item">
                <img src="/logos/mtdpce-logo.png" alt="MTDPCE" />
                <span>MTDPCE</span>
              </div>
              <div className="partner-item">
                <img src="/logos/citadel-logo.png" alt="CITADEL" />
                <span>CITADEL</span>
              </div>
              <div className="partner-item">
                <img src="/logos/lefaso-logo.png" alt="Lefaso.net" />
                <span>Lefaso.net</span>
              </div>
              <div className="partner-item">
                <img src="/logos/fasopresse-logo.png" alt="FasoPresse" />
                <span>FasoPresse</span>
              </div>
              <div className="partner-item">
                <img src="/logos/sidwaya-logo.png" alt="Sidwaya" />
                <span>Sidwaya</span>
              </div>
              <div className="partner-item">
                <img src="/logos/observateur-logo.png" alt="L'Observateur Paalga" />
                <span>L'Observateur Paalga</span>
              </div>
              <div className="partner-item">
                <img src="/logos/aib-logo.png" alt="AIB" />
                <span>AIB</span>
              </div>
            </div>
          </div>
        </section>

        {/* Footer padding for fixed button */}
        <div className="footer-spacer"></div>
      </div>

      {/* Fixed Continue Button */}
      <div className="fixed-button-container">
        <button className="continue-button" onClick={() => navigate('/login')}>
          Continuer
          <span className="arrow">→</span>
        </button>
      </div>
    </div>
  );
}

export default Home;
