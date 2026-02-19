import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { CardsState, Bank, PaymentMethod, Card } from '../types';
import api from '../services/api';

const initialState: CardsState = {
  banks: [],
  paymentMethods: [],
  isLoading: false,
  error: null,
};

export const fetchBanks = createAsyncThunk(
  'cards/fetchBanks',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get<Bank[]>('/cards/banks');
      // Ensure we always return an array
      return Array.isArray(response.data) ? response.data : [];
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch banks');
    }
  }
);

export const fetchPaymentMethods = createAsyncThunk(
  'cards/fetchPaymentMethods',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get<PaymentMethod[]>('/cards/payment-methods');
      // Ensure we always return an array
      return Array.isArray(response.data) ? response.data : [];
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch payment methods');
    }
  }
);

export const addPaymentMethod = createAsyncThunk(
  'cards/addPaymentMethod',
  async (
    data: {
      bank_id: string;
      card_id: string;
      payment_type: string;
      last_four_digits?: string;
      nickname?: string;
    },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.post<PaymentMethod>('/cards/payment-methods', data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add payment method');
    }
  }
);

export const deletePaymentMethod = createAsyncThunk(
  'cards/deletePaymentMethod',
  async (id: string, { rejectWithValue }) => {
    try {
      await api.delete(`/cards/payment-methods/${id}`);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to delete payment method');
    }
  }
);

const cardsSlice = createSlice({
  name: 'cards',
  initialState,
  reducers: {
    clearCardsError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch banks
      .addCase(fetchBanks.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchBanks.fulfilled, (state, action) => {
        state.isLoading = false;
        state.banks = action.payload;
      })
      .addCase(fetchBanks.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch payment methods
      .addCase(fetchPaymentMethods.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchPaymentMethods.fulfilled, (state, action) => {
        state.isLoading = false;
        state.paymentMethods = action.payload;
      })
      .addCase(fetchPaymentMethods.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Add payment method
      .addCase(addPaymentMethod.fulfilled, (state, action) => {
        state.paymentMethods.push(action.payload);
      })
      // Delete payment method
      .addCase(deletePaymentMethod.fulfilled, (state, action) => {
        state.paymentMethods = state.paymentMethods.filter(
          (pm) => pm.id !== action.payload
        );
      });
  },
});

export const { clearCardsError } = cardsSlice.actions;
export default cardsSlice.reducer;
