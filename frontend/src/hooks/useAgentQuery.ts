import { useMutation } from '@tanstack/react-query'
import { agentApi } from '@/lib/api/agent'
import { QueryRequest } from '@/types/agent'

export const useAgentQuery = () => {
  return useMutation({
    mutationFn: (request: QueryRequest) => agentApi.query(request),
  })
}
