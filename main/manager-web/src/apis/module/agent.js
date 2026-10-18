import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

const CALLBACK_RETRY_LIMIT = 10;
const CALLBACK_RETRY_DELAY_MS = 2000;
const CALLBACK_RETRY_WINDOW_MS = CALLBACK_RETRY_LIMIT * CALLBACK_RETRY_DELAY_MS;

function retryCallbackRequest(retry, retryCount, onTerminalFailure, error, retryStartedAt) {
    if (!onTerminalFailure) {
        RequestService.reAjaxFun(() => retry(retryCount + 1))
        return
    }
    const startedAt = retryStartedAt || Date.now()
    if (retryCount >= CALLBACK_RETRY_LIMIT || Date.now() - startedAt >= CALLBACK_RETRY_WINDOW_MS) {
        RequestService.clearRequestTime()
        onTerminalFailure(error)
        return
    }
    setTimeout(() => retry(retryCount + 1, startedAt), CALLBACK_RETRY_DELAY_MS)
}

function attachTerminalFailure(request, onTerminalFailure) {
    if (onTerminalFailure) {
        request.fail((error) => {
            RequestService.clearRequestTime()
            onTerminalFailure(error)
        })
    }
    return request
}

function terminateCallbackRequest(onTerminalFailure, error) {
    RequestService.clearRequestTime()
    if (onTerminalFailure) {
        onTerminalFailure(error)
    }
}


export default {
    // Get the agent list
    getAgentList(callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/list`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentList(callback);
                });
            }).send();
    },
    // Add an agent
    addAgent(agentName, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent`)
            .method('POST')
            .data({ agentName: agentName })
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.addAgent(agentName, callback);
                });
            }).send();
    },
    // Delete an agent
    deleteAgent(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteAgent(agentId, callback);
                });
            }).send();
    },
    // Get the agent configuration
    getDeviceConfig(agentId, callback, onTerminalFailure, retryCount = 0, retryStartedAt = 0) {
        const retryWindowStartedAt = retryStartedAt || Date.now()
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get the configuration:', err);
                retryCallbackRequest(
                    (nextRetryCount, nextRetryStartedAt) => this.getDeviceConfig(
                        agentId,
                        callback,
                        onTerminalFailure,
                        nextRetryCount,
                        nextRetryStartedAt
                    ),
                    retryCount,
                    onTerminalFailure,
                    err,
                    retryWindowStartedAt
                )
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Configure the agent
    updateAgentConfig(agentId, configData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}`)
            .method('PUT')
            .data(configData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateAgentConfig(agentId, configData, callback);
                });
            }).send();
    },
    // Get the agent configuration snapshot list
    getAgentSnapshots(agentId, params, callback, onTerminalFailure, retryCount = 0, retryStartedAt = 0) {
        const retryWindowStartedAt = retryStartedAt || Date.now()
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/snapshots`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((error) => {
                retryCallbackRequest(
                    (nextRetryCount, nextRetryStartedAt) => this.getAgentSnapshots(
                        agentId,
                        params,
                        callback,
                        onTerminalFailure,
                        nextRetryCount,
                        nextRetryStartedAt
                    ),
                    retryCount,
                    onTerminalFailure,
                    error,
                    retryWindowStartedAt
                )
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Get the details of an agent configuration snapshot
    getAgentSnapshot(agentId, snapshotId, callback, onTerminalFailure, retryCount = 0, retryStartedAt = 0) {
        const retryWindowStartedAt = retryStartedAt || Date.now()
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/snapshots/${snapshotId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((error) => {
                retryCallbackRequest(
                    (nextRetryCount, nextRetryStartedAt) => this.getAgentSnapshot(
                        agentId,
                        snapshotId,
                        callback,
                        onTerminalFailure,
                        nextRetryCount,
                        nextRetryStartedAt
                    ),
                    retryCount,
                    onTerminalFailure,
                    error,
                    retryWindowStartedAt
                )
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Restore an agent configuration snapshot
    restoreAgentSnapshot(agentId, snapshotId, currentStateToken, callback, onTerminalFailure) {
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/snapshots/${snapshotId}/restore`)
            .method('POST')
            .data({ currentStateToken })
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((error) => {
                terminateCallbackRequest(onTerminalFailure, error)
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Delete an agent configuration snapshot
    deleteAgentSnapshot(agentId, snapshotId, callback, onTerminalFailure) {
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/snapshots/${snapshotId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((error) => {
                terminateCallbackRequest(onTerminalFailure, error)
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Get the agent template
    getAgentTemplate(callback) {  // The templateName parameter was removed
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get the template:', err);
                RequestService.reAjaxFun(() => {
                    this.getAgentTemplate(callback);
                });
            }).send();
    },

    // Get a paginated list of agent templates
    getAgentTemplatesPage(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template/page`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get the paginated template list:', err);
                RequestService.reAjaxFun(() => {
                    this.getAgentTemplatesPage(params, callback);
                });
            }).send();
    },
    // Get the agent session list
    getAgentSessions(agentId, params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/sessions`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentSessions(agentId, params, callback);
                });
            }).send();
    },
    // Get the agent chat history
    getAgentChatHistory(agentId, sessionId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/chat-history/${sessionId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentChatHistory(agentId, sessionId, callback);
                });
            }).send();
    },
    // Get the audio download ID
    getAudioId(audioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/audio/${audioId}`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAudioId(audioId, callback);
                });
            }).send();
    },
    // Get the MCP access point address of the agent
    getAgentMcpAccessAddress(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/mcp/address/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .fail((err) => {
                callback(err);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentMcpAccessAddress(agentId, callback);
                });
            }).send();
    },
    // Get the MCP tool list of the agent
    getAgentMcpToolsList(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/mcp/tools/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentMcpToolsList(agentId, callback);
                });
            }).send();
    },
    // Add a voiceprint for the agent
    addAgentVoicePrint(voicePrintData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/voice-print`)
            .method('POST')
            .data(voicePrintData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.addAgentVoicePrint(voicePrintData, callback);
                });
            }).send();
    },
    // Get the voiceprint list of a given agent
    getAgentVoicePrintList(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/voice-print/list/${id}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getAgentVoicePrintList(id, callback);
                });
            }).send();
    },
    // Delete an agent voiceprint
    deleteAgentVoicePrint(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/voice-print/${id}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteAgentVoicePrint(id, callback);
                });
            }).send();
    },
    // Update an agent voiceprint
    updateAgentVoicePrint(voicePrintData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/voice-print`)
            .method('PUT')
            .data(voicePrintData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateAgentVoicePrint(voicePrintData, callback);
                });
            }).send();
    },
    // Get the chat history of a given agent for a user type
    getRecentlyFiftyByAgentId(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${id}/chat-history/user`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getRecentlyFiftyByAgentId(id, callback);
                });
            }).send();
    },
    // Get the chat history of a given agent for a user type
    getContentByAudioId(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${id}/chat-history/audio`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getContentByAudioId(id, callback);
                });
            }).send();
    },
    // Methods below were added at the end of the file (after the last method, before the closing brace):
    // Add an agent template
    addAgentTemplate(templateData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template`)
            .method('POST')
            .data(templateData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.addAgentTemplate(templateData, callback);
                });
            }).send();
    },

    // Update an agent template
    updateAgentTemplate(templateData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template`)
            .method('PUT')
            .data(templateData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateAgentTemplate(templateData, callback);
                });
            }).send();
    },

    // Delete an agent template
    deleteAgentTemplate(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template/${id}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteAgentTemplate(id, callback);
                });
            }).send();
    },

    // Batch delete agent templates
    batchDeleteAgentTemplate(ids, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template/batch-remove`) // Updated to the new URL
            .method('POST')
            .data(Array.isArray(ids) ? ids : [ids]) // Make sure the payload is an array
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.batchDeleteAgentTemplate(ids, callback);
                });
            }).send();
    },
    // Method added after getAgentTemplate to get a single template
    getAgentTemplateById(templateId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/template/${templateId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Failed to get the template:', err);
                RequestService.reAjaxFun(() => {
                    this.getAgentTemplateById(templateId, callback);
                });
            }).send();
    },

    // Get the UUID of the chat history download link
    getDownloadUrl(agentId, sessionId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/chat-history/getDownloadUrl/${agentId}/${sessionId}`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getDownloadUrl(agentId, sessionId, callback);
                });
            }).send();
    },
    
    // Search agents
    searchAgent(keyword, searchType, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/list?keyword=${encodeURIComponent(keyword)}&searchType=${searchType}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.searchAgent(keyword, searchType, callback);
                });
            }).send();
    },
    // Get agent tags
    getAgentTags(agentId, callback, onTerminalFailure, retryCount = 0, retryStartedAt = 0) {
        const retryWindowStartedAt = retryStartedAt || Date.now()
        const request = RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/tags`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((error) => {
                retryCallbackRequest(
                    (nextRetryCount, nextRetryStartedAt) => this.getAgentTags(
                        agentId,
                        callback,
                        onTerminalFailure,
                        nextRetryCount,
                        nextRetryStartedAt
                    ),
                    retryCount,
                    onTerminalFailure,
                    error,
                    retryWindowStartedAt
                )
            })
        attachTerminalFailure(request, onTerminalFailure).send();
    },
    // Save agent tags
    saveAgentTags(agentId, tags, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/agent/${agentId}/tags`)
            .method('PUT')
            .data(tags)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.saveAgentTags(agentId, tags, callback);
                });
            }).send();
    },
}
