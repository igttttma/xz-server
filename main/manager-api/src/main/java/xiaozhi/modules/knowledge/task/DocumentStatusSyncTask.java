package xiaozhi.modules.knowledge.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;

/**
 * Scheduled task that synchronizes knowledge base document statuses.
 * 
 * Purpose:
 * 1. Automatically scan documents in "RUNNING" (parsing) state
 * 2. Call the RAGFlow API to obtain the latest status
 * 3. On status transition (RUNNING -> SUCCESS/FAIL), synchronously update the database
 * 4. [Critical] On successful parsing, compensate by updating the knowledge base statistics (TokenCount)
 */
@Component
@AllArgsConstructor
@Slf4j
public class DocumentStatusSyncTask {

    private final KnowledgeFilesService knowledgeFilesService;

    /**
     * Runs the synchronization every 30 seconds.
     * Uses fixedDelay so the next run starts 30 seconds after the previous one finishes, preventing backlog.
     */
    @Scheduled(fixedDelay = 30000)
    public void syncRunningDocuments() {
        try {
            // log.debug("Starting document status synchronization task...");
            knowledgeFilesService.syncRunningDocuments();
        } catch (Exception e) {
            log.error("Document status synchronization task failed", e);
        }
    }
}
