from flask import Flask, render_template, request, jsonify
import time
import threading

app = Flask(__name__)

# Variables globales
num_players = 1
avg_tickets_per_second = 1.0  # Tickets dépensés par joueur par seconde (valeur par défaut)
timer_message = ""
timer_running = False
jackpot_timer_seconds = 0  # Minuteur pour le jackpot
time_between_jackpots = []  # Liste pour stocker les temps entre deux jackpots
last_jackpot_time = 0  # Temps de la dernière activation du jackpot
jackpot_thread = None  # Pour suivre le thread du chronomètre
minuteur_demarree = False


def jackpot_timer():
    global jackpot_timer_seconds, timer_running
    jackpot_timer_seconds = 0
    timer_running = True

    # Incrémente immédiatement avant la première pause
    while timer_running:
        jackpot_timer_seconds += 1
        time.sleep(1)
        if not timer_running:
            break



@app.route("/")
def roue_bouftou():
    global timer_running, jackpot_timer_seconds, minuteur_demarree

    # Réinitialise l'état du minuteur et du démarrage
    timer_running = False
    jackpot_timer_seconds = 0
    minuteur_demarree = False

    # Stoppe explicitement le minuteur pour éviter tout état résiduel
    stop_timer()

    return render_template(
        "roue_bouftou.html",
        num_players=num_players,
        timer_message="00:00",
        time_between_jackpots=time_between_jackpots,
        avg_tickets_per_second=avg_tickets_per_second,
        estimated_time="N/A"
    )


@app.route("/update_players", methods=["POST"])
def update_players():
    global num_players
    action = request.form.get("action")
    if action == "increment":
        num_players += 1
    elif action == "decrement" and num_players > 1:
        num_players -= 1
    return jsonify({"num_players": num_players})

@app.route("/update_tickets", methods=["POST"])
def update_tickets():
    global avg_tickets_per_second
    tickets = request.form.get("tickets")
    try:
        avg_tickets_per_second = float(tickets)
        if avg_tickets_per_second < 0:
            avg_tickets_per_second = 0.0
        elif avg_tickets_per_second > 3:
            avg_tickets_per_second = 3.0
    except ValueError:
        avg_tickets_per_second = 1.0
    return jsonify({"avg_tickets_per_second": avg_tickets_per_second})


@app.route("/calculate_estimate", methods=["GET"])
def calculate_estimate():
    global avg_tickets_per_second, jackpot_timer_seconds, minuteur_demarree

    if not minuteur_demarree:  # Si le minuteur n'a pas commencé
        return jsonify({"estimated_time": "N/A", "remaining_seconds": None})

    if avg_tickets_per_second > 0:
        total_seconds = 1000 / avg_tickets_per_second
        remaining_seconds = total_seconds - jackpot_timer_seconds
        remaining_seconds = max(0, remaining_seconds)  # Empêcher des valeurs négatives
        mins, secs = divmod(int(remaining_seconds), 60)
        estimated_time = f"{mins} min {secs} sec"
    else:
        estimated_time = "N/A"
        remaining_seconds = 0

    return jsonify({
        "estimated_time": estimated_time,
        "remaining_seconds": remaining_seconds,
    })




@app.route("/start_jackpot_timer", methods=["POST"])
def start_jackpot_timer():
    global timer_running, jackpot_thread, jackpot_timer_seconds, minuteur_demarree

    # Active le flag pour démarrer le minuteur
    minuteur_demarree = True

    # Vérifie que le minuteur n'est pas déjà en cours
    if not timer_running:
        jackpot_timer_seconds = 0  # Réinitialise le compteur

        # Arrête tout thread existant (par précaution)
        if jackpot_thread and jackpot_thread.is_alive():
            jackpot_thread.join()

        # Lance un nouveau thread
        jackpot_thread = threading.Thread(target=jackpot_timer)
        jackpot_thread.start()
        timer_running = True

    # Recalcule immédiatement le temps estimé
    if avg_tickets_per_second > 0:
        total_seconds = 1000 / avg_tickets_per_second - jackpot_timer_seconds
        total_seconds = max(0, total_seconds)  # Empêche les valeurs négatives
        mins, secs = divmod(int(total_seconds), 60)
        estimated_time = f"{mins} min {secs} sec"
    else:
        estimated_time = "N/A"

    return jsonify({
        "status": "success",
        "timer_message": "00:00",
        "estimated_time": estimated_time,
    })


@app.route("/stop_timer", methods=["POST"])
def stop_timer():
    global timer_running, jackpot_thread, jackpot_timer_seconds

    if timer_running:
        timer_running = False  # Stop le flag principal
        if jackpot_thread and jackpot_thread.is_alive():
            jackpot_thread.join()  # Arrête le thread backend

    # Réinitialise complètement le minuteur
    jackpot_timer_seconds = 0
    return jsonify({"status": "stopped", "timer_message": "00:00"})



@app.route("/reset", methods=["POST"])
def reset():
    global time_between_jackpots, jackpot_timer_seconds, timer_running, jackpot_thread, minuteur_demarree

    minuteur_demarree = False  # Réinitialise le flag
    if timer_running:
        timer_running = False
        if jackpot_thread and jackpot_thread.is_alive():
            jackpot_thread.join()

    time_between_jackpots = []
    jackpot_timer_seconds = 0
    return jsonify({
        "status": "success",
        "timer_message": "00:00",
        "time_between_jackpots": time_between_jackpots,
    })



@app.route("/get_timer_status", methods=["GET"])
def get_timer_status():
    mins, secs = divmod(jackpot_timer_seconds, 60)
    timer_message = f"{mins:02}:{secs:02}"
    return jsonify({
        "timer_message": timer_message,
        "time_between_jackpots": time_between_jackpots,
    })

if __name__ == "__main__":
    app.run(debug=True)
