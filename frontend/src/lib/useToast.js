import { useCallback, useState } from "react";

export function useToast() {
  const [toast, setToast] = useState(null);
  const show = useCallback((text, type = "ok") => {
    setToast({ text, type });
    setTimeout(() => setToast(null), 4500);
  }, []);
  return [toast, show];
}
