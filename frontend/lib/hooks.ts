'use client';

import { useState, useCallback, useEffect } from 'react';
import { handleAPIError } from './api';

// Hook for React components to use API with loading and error states
export function useAPICall<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (apiCall: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

// Hook specifically for assessment data
export function useAssessment() {
  const [assessmentData, setAssessmentData] = useState(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  // Load data from localStorage only after hydration
  useEffect(() => {
    setIsHydrated(true);
    
    // Load assessment data
    const storedAssessment = localStorage.getItem('portfolioai_assessment');
    if (storedAssessment) {
      try {
        const data = JSON.parse(storedAssessment);
        setAssessmentData(data);
      } catch (error) {
        console.error('Error parsing stored assessment data:', error);
        localStorage.removeItem('portfolioai_assessment');
      }
    }
    
    // Load user ID
    const storedUserId = localStorage.getItem('portfolioai_user_id');
    if (storedUserId) {
      setUserId(storedUserId);
    }
  }, []);

  const saveAssessmentData = useCallback((data: any) => {
    setAssessmentData(data);
    // Store in localStorage for persistence
    if (isHydrated) {
      localStorage.setItem('portfolioai_assessment', JSON.stringify(data));
    }
  }, [isHydrated]);

  const loadAssessmentData = useCallback(() => {
    if (isHydrated) {
      const stored = localStorage.getItem('portfolioai_assessment');
      if (stored) {
        try {
          const data = JSON.parse(stored);
          setAssessmentData(data);
          return data;
        } catch (error) {
          console.error('Error parsing stored assessment data:', error);
          localStorage.removeItem('portfolioai_assessment');
        }
      }
    }
    return null;
  }, [isHydrated]);

  const clearAssessmentData = useCallback(() => {
    setAssessmentData(null);
    setUserId(null);
    if (isHydrated) {
      localStorage.removeItem('portfolioai_assessment');
      localStorage.removeItem('portfolioai_user_id');
    }
  }, [isHydrated]);

  const saveUserId = useCallback((id: string) => {
    setUserId(id);
    if (isHydrated) {
      localStorage.setItem('portfolioai_user_id', id);
    }
  }, [isHydrated]);

  const loadUserId = useCallback(() => {
    if (isHydrated) {
      const stored = localStorage.getItem('portfolioai_user_id');
      if (stored) {
        setUserId(stored);
        return stored;
      }
    }
    return null;
  }, [isHydrated]);

  return {
    assessmentData,
    userId,
    isHydrated,
    saveAssessmentData,
    loadAssessmentData,
    clearAssessmentData,
    saveUserId,
    loadUserId,
  };
}