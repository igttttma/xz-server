package xiaozhi.modules.config.service;

import java.util.List;
import java.util.Map;

public interface ConfigService {
    /**
     * Get the server configuration
     *
     * @param isCache Whether to cache
     * @return Configuration information
     */
    Map<String, Object> getConfig(Boolean isCache);

    /**
     * Get the agent model configuration
     *
     * @param macAddress     MAC address
     * @param selectedModule Models instantiated by the client
     * @return Model configuration information
     */
    Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule);

    /**
     * Get agent replacement words
     *
     * @param macAddress Device MAC address
     * @return Replacement word list, for example ["template1|template01", "template2|template02"]
     */
    List<String> getCorrectWords(String macAddress);
}
