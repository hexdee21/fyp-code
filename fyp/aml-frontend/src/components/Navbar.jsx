import React from "react";
import { Link, useNavigate } from "react-router-dom";


export default function Navbar() {
  const navigate = useNavigate();


  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("wallet_id");
    localStorage.removeItem("email");
    localStorage.removeItem("userRole");


    navigate("/login", { replace: true });
  };


  const isLoggedIn = localStorage.getItem("token");


  return (
    <nav className="bg-gray-800 text-white px-6 py-3 flex justify-between items-center shadow">
      <div className="font-bold text-xl text-red-400">AML Dashboard</div>


      {isLoggedIn && (
        <div className="flex space-x-6">
          <Link to="/dashboard" className="hover:text-red-400">
            Dashboard
          </Link>


          <Link to="/audit" className="hover:text-red-400">
            Audit Logs
          </Link>


          <Link to="/admin" className="hover:text-red-400">
            Admin
          </Link>


          <Link to="/settings" className="hover:text-red-400">
            Settings
          </Link>


          <button
            onClick={handleLogout}
            className="text-red-400 hover:text-white"
          >
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}




