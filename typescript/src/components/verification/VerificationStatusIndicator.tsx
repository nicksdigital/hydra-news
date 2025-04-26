import React from 'react';
import './VerificationStatusIndicator.css';
import VerificationScore from './VerificationScore';
import { verificationLevels, VerificationLevel } from '../../types/NewsContent';

interface VerificationStatusIndicatorProps {
  score?: number;
  level?: VerificationLevel;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
  className?: string;
  onClick?: () => void;
}

/**
 * Component to display verification status with detailed information
 */
const VerificationStatusIndicator: React.FC<VerificationStatusIndicatorProps> = ({
  score,
  level,
  size = 'medium',
  showDetails = true,
  className = '',
  onClick,
}) => {
  // Determine verification level from score if not provided
  const getVerificationLevel = (): VerificationLevel => {
    if (level !== undefined) return level;
    
    if (score === undefined) return VerificationLevel.None;
    
    if (score >= 0.9) return VerificationLevel.Maximum;
    if (score >= 0.7) return VerificationLevel.High;
    if (score >= 0.5) return VerificationLevel.Standard;
    if (score >= 0.3) return VerificationLevel.Minimal;
    return VerificationLevel.None;
  };
  
  const verificationLevel = getVerificationLevel();
  const levelInfo = verificationLevels.find(l => l.level === verificationLevel) || verificationLevels[0];
  
  // Determine if this is clickable
  const isClickable = !!onClick;
  
  return (
    <div 
      className={`verification-status-indicator ${size} ${className} ${isClickable ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="verification-status-header">
        {score !== undefined ? (
          <VerificationScore 
            score={score} 
            size={size} 
            showLabel={false}
          />
        ) : (
          <div 
            className="verification-level-badge"
            style={{ backgroundColor: levelInfo.color }}
          >
            {levelInfo.level}
          </div>
        )}
        
        <div className="verification-level-name" style={{ color: levelInfo.color }}>
          {levelInfo.name}
        </div>
      </div>
      
      {showDetails && (
        <div className="verification-status-details">
          <p className="verification-level-description">
            {levelInfo.description}
          </p>
          
          {score !== undefined && (
            <div className="verification-score-text">
              Verification Score: <span style={{ color: levelInfo.color }}>{Math.round(score * 100)}%</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VerificationStatusIndicator;
