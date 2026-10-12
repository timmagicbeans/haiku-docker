#include <Application.h>
#include <Window.h>
#include <Deskbar.h>
#include <View.h>
#include <PopUpMenu.h>
#include <MenuItem.h>
#include <String.h>
#include <Bitmap.h>
#include <Roster.h>
#include <Entry.h>
#include <Path.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static const char* kReplicantName = "DockerDeskbar";
static const char* kPidFile = "/boot/home/config/settings/docker-vm/vm.pid";

static bool IsVmRunning() {
    FILE* fp = fopen(kPidFile, "r");
    if (!fp) return false;
    pid_t pid = 0;
    if (fscanf(fp, "%d", &pid) != 1 || pid <= 0) {
        fclose(fp);
        return false;
    }
    fclose(fp);
    return (kill(pid, 0) == 0);
}

static void RunDetached(const char* cmd) {
    pid_t pid = fork();
    if (pid == 0) {
        pid_t p2 = fork();
        if (p2 == 0) {
            setsid();
            execl("/bin/sh", "sh", "-c", cmd, (char*)NULL);
            _exit(127);
        }
        _exit(0);
    }
    if (pid > 0) {
        int status;
        waitpid(pid, &status, 0);
    }
}

class _EXPORT DockerDeskbarView : public BView {
public:
    DockerDeskbarView(BRect frame);
    DockerDeskbarView(BMessage* archive);
    virtual ~DockerDeskbarView();

    static BArchivable* Instantiate(BMessage* archive);
    virtual status_t Archive(BMessage* archive, bool deep = true) const;

    virtual void AttachedToWindow();
    virtual void Draw(BRect updateRect);
    virtual void MouseDown(BPoint where);
    virtual void MessageReceived(BMessage* msg);
};

DockerDeskbarView::DockerDeskbarView(BRect frame)
    : BView(frame, kReplicantName, B_FOLLOW_NONE, B_WILL_DRAW)
{
}

DockerDeskbarView::DockerDeskbarView(BMessage* archive)
    : BView(archive)
{
}

DockerDeskbarView::~DockerDeskbarView()
{
}

BArchivable* DockerDeskbarView::Instantiate(BMessage* archive)
{
    if (!validate_instantiation(archive, "DockerDeskbarView"))
        return NULL;
    return new DockerDeskbarView(archive);
}

status_t DockerDeskbarView::Archive(BMessage* archive, bool deep) const
{
    status_t status = BView::Archive(archive, deep);
    archive->AddString("class", "DockerDeskbarView");
    archive->AddString("add_on", "application/x-vnd.Haiku-DockerDeskbar");
    return status;
}

void DockerDeskbarView::AttachedToWindow()
{
    BView::AttachedToWindow();
    SetViewColor(Parent() ? Parent()->ViewColor() : ui_color(B_PANEL_BACKGROUND_COLOR));
}

void DockerDeskbarView::Draw(BRect updateRect)
{
    BRect b = Bounds();
    bool running = IsVmRunning();
    if (running) {
        SetHighColor(0, 120, 215); // Docker Blue
    } else {
        SetHighColor(140, 140, 140); // Inactive Grey
    }
    FillRoundRect(BRect(b.left + 1, b.top + 3, b.right - 1, b.bottom - 2), 3, 3);
    SetHighColor(255, 255, 255);
    FillRect(BRect(b.left + 4, b.top + 5, b.left + 6, b.top + 7));
    FillRect(BRect(b.left + 8, b.top + 5, b.left + 10, b.top + 7));
}

void DockerDeskbarView::MouseDown(BPoint where)
{
    BPopUpMenu* menu = new BPopUpMenu("DockerMenu", false, false);
    bool running = IsVmRunning();
    if (running) {
        menu->AddItem(new BMenuItem("Status: Active (NVMM 1GB)", new BMessage('STAT')));
        menu->AddItem(new BMenuItem("Stop Docker VM", new BMessage('STOP')));
    } else {
        menu->AddItem(new BMenuItem("Status: Stopped", new BMessage('STAT')));
        menu->AddItem(new BMenuItem("Start Docker VM", new BMessage('STRT')));
    }
    menu->AddSeparatorItem();
    menu->AddItem(new BMenuItem("Open /boot/home/dev", new BMessage('ODEV')));
    menu->SetTargetForItems(this);

    ConvertToScreen(&where);
    menu->Go(where, true, false, true);
}

void DockerDeskbarView::MessageReceived(BMessage* msg)
{
    switch (msg->what) {
        case 'STAT': {
            bool r = IsVmRunning();
            if (r) {
                RunDetached("alert 'Docker VM on Haiku: Active (1GB RAM, NVMM Accelerated)'");
            } else {
                RunDetached("alert 'Docker VM on Haiku: Stopped'");
            }
            Invalidate();
            break;
        }
        case 'STRT':
            RunDetached("docker_vm start");
            snooze(1500000);
            Invalidate();
            break;
        case 'STOP':
            RunDetached("docker_vm stop");
            snooze(1500000);
            Invalidate();
            break;
        case 'ODEV':
            RunDetached("open /boot/home/dev");
            break;
        default:
            BView::MessageReceived(msg);
            break;
    }
}

extern "C" _EXPORT BView* instantiate_deskbar_item(float maxWidth, float maxHeight)
{
    float size = (maxHeight > 0.0f) ? maxHeight : 16.0f;
    return new DockerDeskbarView(BRect(0, 0, size - 1.0f, size - 1.0f));
}

int main(int argc, char** argv)
{
    BApplication app("application/x-vnd.Haiku-DockerDeskbar");
    BDeskbar deskbar;
    entry_ref ref;
    if (BEntry("/boot/system/bin/DockerDeskbar").Exists()) {
        get_ref_for_path("/boot/system/bin/DockerDeskbar", &ref);
    } else if (BEntry("/boot/home/config/bin/DockerDeskbar").Exists()) {
        get_ref_for_path("/boot/home/config/bin/DockerDeskbar", &ref);
    } else {
        get_ref_for_path("/boot/home/docker-poc/package_build/bin/DockerDeskbar", &ref);
    }
    int32 id = -1;
    if (deskbar.HasItem(kReplicantName)) {
        deskbar.RemoveItem(kReplicantName);
    }
    status_t res = deskbar.AddItem(&ref, &id);
    printf("Installed DockerDeskbar tray item result: %d, id: %d\n", (int)res, (int)id);
    return (res == B_OK) ? 0 : 1;
}
