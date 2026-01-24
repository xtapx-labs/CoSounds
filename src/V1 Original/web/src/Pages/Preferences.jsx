import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import FullScreenLoader from '../Components/FullScreenLoader';
import styles from './Preferences.module.css';

const Preferences = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isThinking, setIsThinking] = useState(true);

  useEffect(() => {
    const hasCompleted = localStorage.getItem('hasCompletedPreferences') === 'true';
    if (hasCompleted && !location.state?.forcePreferences) {
      navigate('/vote', { replace: true });
    }
  }, [location.state, navigate]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsThinking(false);
    }, 1800);

    return () => clearTimeout(timer);
  }, [location.state]);

  const handleNext = () => {
    navigate('/preferences/0');
  };

  const handleSkip = () => {
    localStorage.setItem('hasCompletedPreferences', 'true');
    sessionStorage.removeItem('preferenceRatings');
    navigate('/vote', { replace: true });
  };

  if (isThinking) {
    return <FullScreenLoader message="Compiling your favourites..." />;
  }

  return (
    <div className={styles['preferences-page']}>
      <div className={styles['preferences-background']}>
        <div className={`${styles.glow} ${styles['glow-1']}`}></div>
        <div className={`${styles.glow} ${styles['glow-2']}`}></div>
      </div>

      <div className={styles['preferences-card']}>
        <div className={styles['card-header']}>
          <span className={styles['card-pill']}>Step 1 of 6</span>
          <h1 className={styles['card-title']}>Your personalized palette</h1>
          <p className={styles['card-subtitle']}>
            Let's discover your sound preferences and create a personalized experience.
          </p>
        </div>


        <div className={styles['card-footer']}>
          <button onClick={handleSkip} className={styles['skip-button']}>
            Skip survey
          </button>
          <button onClick={handleNext} className={styles['next-button']}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default Preferences;

