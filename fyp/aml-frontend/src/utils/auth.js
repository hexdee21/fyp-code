// src/utils/auth.js
export const setAuth = ({ token }) => {
    if (token) {
      localStorage.setItem("token", token);
      localStorage.setItem("isAuthenticated", "true");
    }
  };
  
  export const clearAuth = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("isAuthenticated");
  };
  
  export const isAuthenticated = () => {
    return localStorage.getItem("isAuthenticated") === "true";
  };
  
  export const getToken = () => localStorage.getItem("token");
  