/**
 * API service layer for communicating with the backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Project API
export const projectAPI = {
  create: (data: { name: string; description?: string }) =>
    api.post('/projects/', data),

  get: (projectId: number) =>
    api.get(`/projects/${projectId}`),

  list: (skip = 0, limit = 100) =>
    api.get('/projects/', { params: { skip, limit } }),

  update: (projectId: number, data: { name?: string; description?: string }) =>
    api.put(`/projects/${projectId}`, data),

  delete: (projectId: number) =>
    api.delete(`/projects/${projectId}`),

  createAOI: (projectId: number, data: { name: string; geojson: any }) =>
    api.post(`/projects/${projectId}/aoi`, data),

  getAOIs: (projectId: number) =>
    api.get(`/projects/${projectId}/aoi`),
};

// Analysis API
export const analysisAPI = {
  runAnalysis: (
    projectId: number,
    aoiId: number,
    data: {
      weights_json: Record<string, number>;
      constraints_json: Record<string, any>;
    }
  ) => api.post(`/analysis/${projectId}/run?aoi_id=${aoiId}`, data),

  getStatus: (jobId: number) =>
    api.get(`/analysis/${jobId}/status`),

  getResults: (jobId: number) =>
    api.get(`/analysis/${jobId}/results`),

  listJobs: (projectId: number) =>
    api.get(`/analysis/${projectId}/jobs`),

  deleteJob: (jobId: number) =>
    api.delete(`/analysis/${jobId}`),
};

// Data Query API (Parcel Inspector)
export const dataAPI = {
  queryPoint: (lat: number, lon: number) =>
    api.get('/data/point', { params: { lat, lon } }),

  listLayers: () =>
    api.get('/data/layers'),
};

export default api;
