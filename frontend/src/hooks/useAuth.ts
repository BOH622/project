import { useQuery } from "@tanstack/react-query";

import { fetchCurrentUser } from "@/lib/auth";

export function useAuth() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: fetchCurrentUser,
    staleTime: 60_000,
  });
}
