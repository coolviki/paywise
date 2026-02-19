import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import cardsReducer from './cardsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    cards: cardsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
