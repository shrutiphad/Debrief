import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import LogInteractionScreen from "./components/LogInteractionScreen";
import { fetchHCPs } from "./store/slices/hcpSlice";

export default function App() {
  const dispatch = useDispatch();
  const hcpStatus = useSelector((s) => s.hcps.status);

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main">
        <Topbar />
        <div className="content">
          {hcpStatus === "failed" && (
            <div className="empty-state">
              Couldn't reach the backend API. Make sure it's running at the URL in your frontend .env
              (VITE_API_URL) — see README.md.
            </div>
          )}
          {hcpStatus === "succeeded" && <LogInteractionScreen />}
        </div>
      </div>
    </div>
  );
}
