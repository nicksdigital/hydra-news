import React from 'react';
import './VerificationScore.css';

interface VerificationScoreProps {
  score: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  className?: string;
}

/**
 * Component to display a verification score as a circular gauge
 */
const VerificationScore: React.FC<VerificationScoreProps> = ({
  score,
  size = 'medium',
  showLabel = true,
  className = '',
}) => {
  // Normalize score to 0-100 range
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score * 100)));
  
  // Calculate SVG parameters based on size
  const dimensions = {
    small: { size: 40, strokeWidth: 4, fontSize: 12 },
    medium: { size: 80, strokeWidth: 6, fontSize: 24 },
    large: { size: 120, strokeWidth: 8, fontSize: 36 },
  };
  
  const { size: sizeValue, strokeWidth, fontSize } = dimensions[size];
  const radius = (sizeValue - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - normalizedScore / 100);
  
  // Determine color based on score
  const getColor = () => {
    if (normalizedScore >= 80) return '#4CAF50'; // Green
    if (normalizedScore >= 60) return '#8BC34A'; // Light Green
    if (normalizedScore >= 40) return '#FFC107'; // Amber
    if (normalizedScore >= 20) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };
  
  // Get label text based on score
  const getLabel = () => {
    if (normalizedScore >= 80) return 'Verified';
    if (normalizedScore >= 60) return 'Likely True';
    if (normalizedScore >= 40) return 'Uncertain';
    if (normalizedScore >= 20) return 'Questionable';
    return 'Disputed';
  };
  
  return (
    <div className={`verification-score ${size} ${className}`}>
      <svg
        width={sizeValue}
        height={sizeValue}
        viewBox={`0 0 ${sizeValue} ${sizeValue}`}
        className="verification-score-svg"
      >
        {/* Background circle */}
        <circle
          cx={sizeValue / 2}
          cy={sizeValue / 2}
          r={radius}
          fill="transparent"
          stroke="#e6e6e6"
          strokeWidth={strokeWidth}
        />
        
        {/* Progress circle */}
        <circle
          cx={sizeValue / 2}
          cy={sizeValue / 2}
          r={radius}
          fill="transparent"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${sizeValue / 2} ${sizeValue / 2})`}
        />
        
        {/* Score text */}
        <text
          x="50%"
          y="50%"
          dy=".35em"
          textAnchor="middle"
          fill={getColor()}
          fontSize={fontSize}
          fontWeight="bold"
        >
          {normalizedScore}
        </text>
      </svg>
      
      {showLabel && <div className="verification-label" style={{ color: getColor() }}>{getLabel()}</div>}
    </div>
  );
};

export default VerificationScore;
