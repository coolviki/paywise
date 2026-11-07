import api from './api';
import { McpKey, McpKeyCreated } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const MCP_CONNECTOR_URL = `${API_URL.replace(/\/$/, '')}/mcp`;

export const mcpKeyService = {
  async list(): Promise<McpKey[]> {
    const res = await api.get<McpKey[]>('/mcp-keys');
    return res.data;
  },

  async create(name: string): Promise<McpKeyCreated> {
    const res = await api.post<McpKeyCreated>('/mcp-keys', { name });
    return res.data;
  },

  async revoke(id: string): Promise<void> {
    await api.delete(`/mcp-keys/${id}`);
  },
};
