package xiaozhi.modules.agent.service;


import java.util.List;

/**
 * Agent MCP access point service
 *
 * @author zjy
 */
public interface AgentMcpAccessPointService {
    /**
     * Get the MCP access point address of the agent
     * @param id Agent ID
     * @return MCP access point address
     */
   String getAgentMcpAccessAddress(String id);

    /**
     * Get the existing tool list of the agent's MCP access point
     * @param id Agent ID
     * @return Tool list
     */
   List<String> getAgentMcpToolsList(String id);
}
