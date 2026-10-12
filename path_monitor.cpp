#include <Application.h>
#include <Handler.h>
#include <Messenger.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <private/storage/PathMonitor.h>

using namespace BPrivate;

class PMHandler : public BHandler {
public:
    PMHandler() : BHandler("PMHandler") {}
    virtual void MessageReceived(BMessage* message) {
        if (message->what == B_PATH_MONITOR) {
            const char* path = NULL;
            if (message->FindString("path", &path) == B_OK && path != NULL) {
                printf("%s\n", path);
                fflush(stdout);
            }
        } else {
            BHandler::MessageReceived(message);
        }
    }
};

int main(int argc, char** argv) {
    const char* watchPath = (argc > 1) ? argv[1] : "/boot/home/dev";
    BApplication app("application/x-vnd.Haiku-PathMonitorBridge");
    PMHandler handler;
    app.AddHandler(&handler);
    BMessenger msgr(&handler);
    status_t res = BPathMonitor::StartWatching(watchPath,
        B_WATCH_RECURSIVELY | B_WATCH_STAT | B_WATCH_NAME, msgr);
    if (res != B_OK) {
        fprintf(stderr, "Failed to start BPathMonitor on %s: %d\n", watchPath, (int)res);
        return 1;
    }
    fprintf(stderr, "BPathMonitor listening on %s\n", watchPath);
    app.Run();
    return 0;
}
