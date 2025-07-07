import streamlit as st
import chess
import chess.svg
import random
import time
import base64
from io import BytesIO

# Configure page
st.set_page_config(
    page_title="♟️ Chess Wizard",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .game-stats {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    
    .chess-board {
        border: 5px solid #8B4513;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin: 1rem auto;
        display: block;
        max-width: 500px;
        cursor: pointer;
    }
    
    .chess-board svg {
        cursor: pointer;
    }
    
    .chess-square {
        cursor: pointer !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .game-board-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .move-input-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .instructions {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: left;
    }
    
    .selected-square {
        background-color: #ffff00 !important;
        opacity: 0.7;
    }
    
    .legal-move-square {
        background-color: #90EE90 !important;
        opacity: 0.5;
    }
    
    .click-instruction {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'game_mode' not in st.session_state:
    st.session_state.game_mode = None
if 'player_color' not in st.session_state:
    st.session_state.player_color = None
if 'move_history' not in st.session_state:
    st.session_state.move_history = []
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'winner' not in st.session_state:
    st.session_state.winner = None
if 'ai_thinking' not in st.session_state:
    st.session_state.ai_thinking = False
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'last_move' not in st.session_state:
    st.session_state.last_move = None
if 'legal_moves_for_piece' not in st.session_state:
    st.session_state.legal_moves_for_piece = []

def reset_game():
    """Reset the game state"""
    st.session_state.board = chess.Board()
    st.session_state.move_history = []
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.ai_thinking = False
    st.session_state.selected_square = None
    st.session_state.last_move = None
    st.session_state.legal_moves_for_piece = []

def get_board_svg():
    """Generate SVG representation of the chess board with clickable squares"""
    highlighted_squares = {}
    
    # Highlight selected square
    if st.session_state.selected_square is not None:
        highlighted_squares[st.session_state.selected_square] = '#ffff0070'
    
    # Highlight legal moves for selected piece
    for move in st.session_state.legal_moves_for_piece:
        highlighted_squares[move.to_square] = '#90EE9070'
    
    flipped = st.session_state.player_color == chess.BLACK
    board_svg = chess.svg.board(
        st.session_state.board, 
        flipped=flipped, 
        size=500,
        fill=highlighted_squares,
        lastmove=st.session_state.last_move
    )
    
    # Add click handlers to the SVG
    board_svg = add_click_handlers(board_svg)
    return board_svg

def add_click_handlers(svg_content):
    """Add JavaScript click handlers to the chess board SVG"""
    # Add JavaScript for handling clicks
    click_script = """
    <script>
    function handleSquareClick(square) {
        // Send the clicked square to Streamlit
        const event = new CustomEvent('squareClick', {detail: square});
        window.dispatchEvent(event);
        
        // Also try to trigger a form submission to update the state
        const form = document.querySelector('form');
        if (form) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'clicked_square';
            input.value = square;
            form.appendChild(input);
            form.submit();
        }
    }
    
    // Add click listeners to all squares
    document.addEventListener('DOMContentLoaded', function() {
        const squares = document.querySelectorAll('.chess-board rect');
        squares.forEach(function(square, index) {
            square.style.cursor = 'pointer';
            square.addEventListener('click', function() {
                const file = String.fromCharCode(97 + (index % 8));
                const rank = Math.floor(index / 8) + 1;
                const squareName = file + rank;
                handleSquareClick(squareName);
            });
        });
    });
    </script>
    """
    
    return svg_content + click_script

def make_ai_move():
    """Make AI move using simple evaluation"""
    if st.session_state.board.is_game_over():
        return
    
    st.session_state.ai_thinking = True
    
    # Simple AI: prioritize captures, then random moves
    legal_moves = list(st.session_state.board.legal_moves)
    
    # Prioritize captures
    capture_moves = []
    for move in legal_moves:
        if st.session_state.board.is_capture(move):
            capture_moves.append(move)
    
    if capture_moves:
        move = random.choice(capture_moves)
    else:
        move = random.choice(legal_moves)
    
    st.session_state.board.push(move)
    st.session_state.move_history.append(move.uci())
    st.session_state.last_move = move
    st.session_state.ai_thinking = False
    
    check_game_over()

def check_game_over():
    """Check if the game is over"""
    if st.session_state.board.is_game_over():
        st.session_state.game_over = True
        if st.session_state.board.is_checkmate():
            if st.session_state.board.turn == chess.WHITE:
                st.session_state.winner = "Black wins by checkmate!"
            else:
                st.session_state.winner = "White wins by checkmate!"
        elif st.session_state.board.is_stalemate():
            st.session_state.winner = "Draw by stalemate!"
        elif st.session_state.board.is_insufficient_material():
            st.session_state.winner = "Draw by insufficient material!"
        else:
            st.session_state.winner = "Draw!"

def handle_square_click(square_name):
    """Handle clicking on a chess square"""
    if st.session_state.game_over:
        return
    
    square_index = chess.parse_square(square_name)
    
    # If no square is selected, select this square if it has a piece
    if st.session_state.selected_square is None:
        piece = st.session_state.board.piece_at(square_index)
        if piece and piece.color == st.session_state.board.turn:
            st.session_state.selected_square = square_index
            # Get legal moves for this piece
            st.session_state.legal_moves_for_piece = [
                move for move in st.session_state.board.legal_moves 
                if move.from_square == square_index
            ]
    else:
        # A square is already selected
        if square_index == st.session_state.selected_square:
            # Clicking the same square - deselect
            st.session_state.selected_square = None
            st.session_state.legal_moves_for_piece = []
        else:
            # Try to make a move
            try:
                move = chess.Move(st.session_state.selected_square, square_index)
                
                # Check for pawn promotion
                piece = st.session_state.board.piece_at(st.session_state.selected_square)
                if (piece and piece.piece_type == chess.PAWN):
                    if (square_index // 8 == 7 and st.session_state.board.turn == chess.WHITE) or \
                       (square_index // 8 == 0 and st.session_state.board.turn == chess.BLACK):
                        move.promotion = chess.QUEEN
                
                if move in st.session_state.board.legal_moves:
                    # Valid move
                    st.session_state.board.push(move)
                    st.session_state.move_history.append(move.uci())
                    st.session_state.last_move = move
                    st.session_state.selected_square = None
                    st.session_state.legal_moves_for_piece = []
                    check_game_over()
                    
                    # AI move for computer mode
                    if (st.session_state.game_mode == "🤖 Play vs Computer" and 
                        not st.session_state.game_over and
                        st.session_state.board.turn != st.session_state.player_color):
                        time.sleep(0.5)
                        make_ai_move()
                else:
                    # Invalid move - try to select the new square instead
                    piece = st.session_state.board.piece_at(square_index)
                    if piece and piece.color == st.session_state.board.turn:
                        st.session_state.selected_square = square_index
                        st.session_state.legal_moves_for_piece = [
                            move for move in st.session_state.board.legal_moves 
                            if move.from_square == square_index
                        ]
                    else:
                        st.session_state.selected_square = None
                        st.session_state.legal_moves_for_piece = []
            except:
                # Invalid move - deselect
                st.session_state.selected_square = None
                st.session_state.legal_moves_for_piece = []

def square_name_to_index(square_name):
    """Convert square name (e.g., 'e4') to square index"""
    try:
        return chess.parse_square(square_name)
    except:
        return None

# Check for game start
if st.session_state.game_mode and st.session_state.player_color and not st.session_state.game_started:
    st.session_state.game_started = True

# Main interface logic
if not st.session_state.game_started:
    # Setup screen
    st.markdown("""
    <div class="main-header">
        <h1>♟️ Chess Wizard</h1>
        <p style="color: white; font-size: 1.2rem;">Master the Game of Kings</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎮 Game Setup")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Choose Game Mode")
        if st.button("🤖 Play vs Computer", key="vs_computer", use_container_width=True):
            st.session_state.game_mode = "🤖 Play vs Computer"
            st.rerun()
    
    with col2:
        st.markdown("#### Choose Game Mode")
        if st.button("👥 Play vs Human", key="vs_human", use_container_width=True):
            st.session_state.game_mode = "👥 Play vs Human"
            st.rerun()
    
    with col3:
        st.markdown("#### Game Features")
        st.markdown("""
        - **Click to move pieces**
        - Beautiful interactive chess board
        - Real-time game stats
        - Move history tracking
        - Legal move highlighting
        """)
    
    if st.session_state.game_mode:
        st.markdown("---")
        st.markdown("### 🎨 Choose Your Color")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚪ Play as White", key="white", use_container_width=True):
                st.session_state.player_color = chess.WHITE
                reset_game()
                st.rerun()
        
        with col2:
            if st.button("⚫ Play as Black", key="black", use_container_width=True):
                st.session_state.player_color = chess.BLACK
                reset_game()
                # If playing as black vs computer, make AI move first
                if st.session_state.game_mode == "🤖 Play vs Computer":
                    make_ai_move()
                st.rerun()

else:
    # Game screen
    st.markdown("""
    <div class="game-board-container">
        <h2 style="color: white; margin-bottom: 1rem;">♟️ Chess Wizard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Game controls row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🏠 Menu", key="menu"):
            st.session_state.game_started = False
            st.session_state.game_mode = None
            st.session_state.player_color = None
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset", key="reset_game"):
            reset_game()
            st.rerun()
    
    with col3:
        if st.button("↩️ Undo", key="undo_move"):
            if len(st.session_state.move_history) > 0:
                st.session_state.board.pop()
                st.session_state.move_history.pop()
                st.session_state.game_over = False
                st.session_state.winner = None
                st.session_state.selected_square = None
                st.session_state.legal_moves_for_piece = []
                # If vs computer, undo AI move too
                if (st.session_state.game_mode == "🤖 Play vs Computer" and 
                    len(st.session_state.move_history) > 0):
                    st.session_state.board.pop()
                    st.session_state.move_history.pop()
                st.rerun()
    
    with col4:
        # Game status
        if st.session_state.game_over:
            st.success(f"🎉 {st.session_state.winner}")
        elif st.session_state.ai_thinking:
            st.info("🤔 AI thinking...")
        elif st.session_state.board.is_check():
            st.warning("⚠️ Check!")
        else:
            current_player = "White" if st.session_state.board.turn == chess.WHITE else "Black"
            st.info(f"🎯 {current_player}'s turn")
    
    with col5:
        # Game info
        st.markdown(f"""
        **Mode:** {st.session_state.game_mode}  
        **Your Color:** {'White' if st.session_state.player_color == chess.WHITE else 'Black'}  
        **Moves:** {len(st.session_state.move_history)}
        """)
    
    # Click instruction
    if not st.session_state.game_over:
        if st.session_state.selected_square is not None:
            square_name = chess.square_name(st.session_state.selected_square)
            st.markdown(f"""
            <div class="click-instruction">
                ✨ Piece selected on {square_name.upper()}! Click on a highlighted square to move, or click the same square to deselect.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="click-instruction">
                🖱️ Click on a piece to select it, then click on a destination square to move!
            </div>
            """, unsafe_allow_html=True)
    
    # Chess board
    st.markdown("### 🏁 Interactive Chess Board")
    board_svg = get_board_svg()
    st.markdown(f'<div class="chess-board">{board_svg}</div>', unsafe_allow_html=True)
    
    # Alternative move input section (for backup)
    if not st.session_state.game_over:
        with st.expander("🎯 Alternative Move Input (Text-based)", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                from_square = st.text_input(
                    "From square (e.g., e2):",
                    key="from_square",
                    placeholder="e2"
                )
            
            with col2:
                to_square = st.text_input(
                    "To square (e.g., e4):",
                    key="to_square",
                    placeholder="e4"
                )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("▶️ Make Move", key="make_move"):
                    if from_square and to_square:
                        from_idx = square_name_to_index(from_square)
                        to_idx = square_name_to_index(to_square)
                        
                        if from_idx is not None and to_idx is not None:
                            try:
                                move = chess.Move(from_idx, to_idx)
                                
                                # Check for pawn promotion
                                piece = st.session_state.board.piece_at(from_idx)
                                if (piece and piece.piece_type == chess.PAWN):
                                    if (to_idx // 8 == 7 and st.session_state.board.turn == chess.WHITE) or \
                                       (to_idx // 8 == 0 and st.session_state.board.turn == chess.BLACK):
                                        move.promotion = chess.QUEEN
                                
                                if move in st.session_state.board.legal_moves:
                                    st.session_state.board.push(move)
                                    st.session_state.move_history.append(move.uci())
                                    st.session_state.last_move = move
                                    st.session_state.selected_square = None
                                    st.session_state.legal_moves_for_piece = []
                                    check_game_over()
                                    
                                    # Clear input fields
                                    st.session_state.from_square = ""
                                    st.session_state.to_square = ""
                                    
                                    # AI move for computer mode
                                    if (st.session_state.game_mode == "🤖 Play vs Computer" and 
                                        not st.session_state.game_over and
                                        st.session_state.board.turn != st.session_state.player_color):
                                        time.sleep(0.5)
                                        make_ai_move()
                                    
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid move! Please try again.")
                            except Exception as e:
                                st.error("❌ Invalid move format!")
                        else:
                            st.error("❌ Invalid square names!")
            
            with col2:
                if st.button("🔍 Show Legal Moves", key="show_moves"):
                    legal_moves = [move.uci() for move in st.session_state.board.legal_moves]
                    st.info(f"Legal moves: {', '.join(legal_moves[:10])}")
                    if len(legal_moves) > 10:
                        st.info(f"... and {len(legal_moves) - 10} more")
            
            with col3:
                if st.button("💡 Get Hint", key="get_hint"):
                    legal_moves = list(st.session_state.board.legal_moves)
                    if legal_moves:
                        hint_move = random.choice(legal_moves)
                        from_square = chess.square_name(hint_move.from_square)
                        to_square = chess.square_name(hint_move.to_square)
                        st.info(f"💡 Try: {from_square} to {to_square}")
    
    # Instructions
    st.markdown("""
    <div class="instructions">
        <h4>🎯 How to Play</h4>
        <ul>
            <li><strong>Click to move:</strong> Click on a piece to select it, then click on a destination square</li>
            <li><strong>Visual feedback:</strong> Selected pieces are highlighted in yellow, legal moves in green</li>
            <li><strong>Deselect:</strong> Click on the same piece again to deselect it</li>
            <li><strong>Special moves:</strong> Pawn promotion is automatic to Queen</li>
            <li><strong>Alternative input:</strong> Use the text input section as backup</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Move history
    if st.session_state.move_history:
        st.markdown("### 📜 Move History")
        history_text = ""
        for i, move in enumerate(st.session_state.move_history):
            if i % 2 == 0:
                history_text += f"{i//2 + 1}. {move} "
            else:
                history_text += f"{move}  "
        st.code(history_text)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>♟️ Chess Wizard - Master the Game of Kings ♟️</p>
    <p>Built with Streamlit & Python-Chess</p>
</div>
""", unsafe_allow_html=True)
